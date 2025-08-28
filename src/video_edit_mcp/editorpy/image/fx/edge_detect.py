import cv2


def edge_detect(clip):
    # 转换为灰度图
    gray = cv2.cvtColor(clip, cv2.COLOR_RGB2GRAY)
    
    # 使用 Canny 边缘检测
    edges = cv2.Canny(gray, 100, 200)
    
    # 反转（边缘为白色，背景为黑色）
    edges = 255 - edges
    
    # 转换回 RGB
    edge_rgb = cv2.cvtColor(edges, cv2.COLOR_GRAY2RGB)
    
    return edge_rgb