# server/fusion.py
import numpy as np
import cv2

def guided_detail_injection(opt_rgb, therm_gray, alpha=0.8, blur_sigma=5, edge_dilate=3):
    """
    opt_rgb: HxWx3 uint8 (0-255) high-res optical RGB image
    therm_gray: h'xw' single-band thermal grayscale image (uint8 or float)
    Returns fused_rgb: HxWx3 uint8 (visualized thermal fused with guidance)
    and fused_thermal (float) same size as opt, in original thermal units normalized to 0..1
    """

    # Ensure optical is float32
    opt = opt_rgb.astype(np.float32) / 255.0

    # Convert thermal to float32 0..1
    t = therm_gray.astype(np.float32)
    if t.max() > 2:  # likely uint8 0-255 or actual temps; normalize to 0..1
        t = (t - t.min()) / (t.max() - t.min() + 1e-8)
    else:
        # assume already 0..1
        t = np.clip(t, 0.0, 1.0)

    # Upsample thermal to optical size
    H, W = opt.shape[:2]
    t_up = cv2.resize(t, (W, H), interpolation=cv2.INTER_CUBIC)

    # Build guidance: optical luminance
    lum = 0.299 * opt[...,0] + 0.587 * opt[...,1] + 0.114 * opt[...,2]

    # Smooth luminance to get base
    ksize = int(max(3, (blur_sigma*4)//2*2+1))
    base = cv2.GaussianBlur(lum, (ksize, ksize), blur_sigma)

    # High-frequency detail of optical
    detail = lum - base

    # Edge mask from optical (Canny on scaled luminance)
    lum_8 = np.uint8(np.clip(lum*255.0, 0, 255))
    edges = cv2.Canny(lum_8, 50, 150)
    # Dilate edges for a thicker mask
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (edge_dilate, edge_dilate))
    mask = cv2.dilate(edges, kernel, iterations=1).astype(np.float32) / 255.0

    # Soft mask from gradient magnitude (so we don't only inject on thin edges)
    gx = cv2.Sobel(lum, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(lum, cv2.CV_32F, 0, 1, ksize=3)
    grad = np.sqrt(gx*gx + gy*gy)
    grad = grad / (grad.max()+1e-8)
    soft_mask = np.clip(grad*2.0, 0, 1)  # amplify a bit

    # Combine hard edge mask and soft gradient
    combined_mask = np.clip(mask + 0.6*soft_mask, 0, 1)

    # Normalize detail to have reasonable amplitude relative to thermal range
    d_std = detail.std() if detail.std() > 1e-8 else 1.0
    # scale factor such that detail injection doesn't dominate: alpha * (detail/d_std) * 0.03
    detail_scaled = (detail / d_std) * 0.05

    # Inject detail only where combined_mask > 0
    fused_t = t_up + alpha * detail_scaled * combined_mask

    # Clip fused thermal to 0..1
    fused_t = np.clip(fused_t, 0.0, 1.0)

    # Create colored visualization (apply matplotlib colormap)
    import matplotlib.cm as cm
    cmap = cm.get_cmap('inferno')  # or 'jet','magma'
    fused_rgb = cmap(fused_t)[:, :, :3]  # returns floats 0..1
    fused_rgb = np.uint8(np.clip(fused_rgb * 255.0, 0, 255))

    return fused_rgb, fused_t, combined_mask
