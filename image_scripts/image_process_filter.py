import cv2
import numpy as np
import argparse
import json
import os
from datetime import datetime

# Global variables for image processing parameters
class Params:
    # Bilateral filter parameters
    bilateral_d = 9        # Diameter of each pixel neighborhood (must be odd)
    bilateral_sigma_color = 75  # Filter sigma in the color space
    bilateral_sigma_space = 75  # Filter sigma in the coordinate space
    
    # Brightness and contrast parameters
    alpha = 100  # Contrast (100 = 1.0)
    beta = 0    # Brightness (0-100)
    
    # Gamma correction parameter
    gamma = 100  # Gamma value (100 = 1.0)
    
    def to_dict(self):
        return {
            'bilateral_d': self.bilateral_d,
            'bilateral_sigma_color': self.bilateral_sigma_color,
            'bilateral_sigma_space': self.bilateral_sigma_space,
            'alpha': self.alpha,
            'beta': self.beta,
            'gamma': self.gamma
        }

params = Params()

def simple_white_balance(img):
    """
    Simple white balance implementation using the gray world assumption
    """
    b, g, r = cv2.split(img)
    r_avg = cv2.mean(r)[0]
    g_avg = cv2.mean(g)[0]
    b_avg = cv2.mean(b)[0]
    
    k = (r_avg + g_avg + b_avg) / 3
    kr = k / r_avg if r_avg > 0 else 1
    kg = k / g_avg if g_avg > 0 else 1
    kb = k / b_avg if b_avg > 0 else 1
    
    r = cv2.multiply(r, kr)
    g = cv2.multiply(g, kg)
    b = cv2.multiply(b, kb)
    
    return cv2.merge([b, g, r])

def process_frame(raw):
    """
    Processes an input image with current parameter values
    """
    try:
        # Check if image is valid
        if raw is None or raw.size == 0:
            print("Invalid input image")
            return raw

        # Make a copy to avoid modifying the original
        image = raw.copy()
        
        print(f"Processing image - Initial shape: {image.shape}, Mean: {np.mean(image)}")

        # Skip white balance for now as it might be causing issues
        # balanced_image = simple_white_balance(image)
        balanced_image = image

        # Denoise the image
        denoised_image = cv2.bilateralFilter(balanced_image, 
                                            params.bilateral_d,
                                            params.bilateral_sigma_color, 
                                            params.bilateral_sigma_space)
        print(f"After denoising - Mean: {np.mean(denoised_image)}")

        # Adjust brightness and contrast
        alpha = max(params.alpha / 100.0, 0.01)  # Convert to float
        beta = params.beta
        adjusted_image = cv2.convertScaleAbs(denoised_image, alpha=alpha, beta=beta)
        print(f"After brightness/contrast - Mean: {np.mean(adjusted_image)}")

        # Apply gamma correction
        gamma = max(params.gamma / 100.0, 0.01)  # Convert to float
        inv_gamma = 1.0 / gamma
        table = np.array([(i / 255.0) ** inv_gamma * 255 for i in range(256)]).astype("uint8")
        gamma_corrected_image = cv2.LUT(adjusted_image, table)
        print(f"After gamma correction - Mean: {np.mean(gamma_corrected_image)}")
            
        print(f"Final image - Mean: {np.mean(gamma_corrected_image)}")
        
        # Ensure the output is valid
        if np.mean(gamma_corrected_image) == 0:
            print("Warning: Output image is black, returning original")
            return raw
            
        return gamma_corrected_image

    except Exception as e:
        print(f"Error in processing: {e}")
        return raw

def on_trackbar_change(x):
    """Callback function for trackbar changes"""
    global original_image
    
    # Get current parameter values
    params.alpha = cv2.getTrackbarPos('Contrast', 'Image Processing')
    params.beta = cv2.getTrackbarPos('Brightness', 'Image Processing')
    params.gamma = cv2.getTrackbarPos('Gamma', 'Image Processing')
    params.bilateral_d = max(1, cv2.getTrackbarPos('Bilateral D', 'Image Processing'))
    params.bilateral_sigma_color = cv2.getTrackbarPos('Bilateral Color', 'Image Processing')
    params.bilateral_sigma_space = cv2.getTrackbarPos('Bilateral Space', 'Image Processing')
    
    # Process and display the image
    processed = process_frame(original_image)
    if processed is not None:
        cv2.imshow('Image Processing', processed)

def save_results(input_path, processed_image):
    """Save the processed image and parameters"""
    # Create timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Get the input filename without extension
    base_name = os.path.splitext(os.path.basename(input_path))[0]
    
    # Save processed image
    output_image_path = os.path.join('color_tuned_images', f'{base_name}_processed_{timestamp}.jpg')
    cv2.imwrite(output_image_path, processed_image)
    print(f"Saved processed image to: {output_image_path}")
    
    # Save parameters to JSON
    params_dict = params.to_dict()
    output_params_path = os.path.join('color_tuned_images', f'{base_name}_params_{timestamp}.json')
    with open(output_params_path, 'w') as f:
        json.dump(params_dict, f, indent=4)
    print(f"Saved parameters to: {output_params_path}")

def main():
    global original_image
    
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Interactive image processing')
    parser.add_argument('input_image', help='Path to the input JPG image')
    args = parser.parse_args()

    # Read the input image
    print(f"Attempting to load image from: {args.input_image}")
    original_image = cv2.imread(args.input_image)
    
    if original_image is None:
        print(f"Error: Could not read image at {args.input_image}")
        return

    print(f"Image loaded successfully: {original_image.shape}")

    # Create window and show original image first
    cv2.namedWindow('Image Processing', cv2.WINDOW_NORMAL)
    cv2.imshow('Image Processing', original_image)
    cv2.waitKey(100)  # Wait a bit to ensure window is created
    
    # Create trackbars with valid ranges
    cv2.createTrackbar('Contrast', 'Image Processing', 100, 200, on_trackbar_change)  # 0-200%
    cv2.createTrackbar('Brightness', 'Image Processing', 0, 100, on_trackbar_change)  # 0-100
    cv2.createTrackbar('Gamma', 'Image Processing', 100, 200, on_trackbar_change)    # 0-200%
    cv2.createTrackbar('Bilateral D', 'Image Processing', 9, 15, on_trackbar_change) # 3-15
    cv2.createTrackbar('Bilateral Color', 'Image Processing', 75, 150, on_trackbar_change)
    cv2.createTrackbar('Bilateral Space', 'Image Processing', 75, 150, on_trackbar_change)

    # Set initial values
    params.alpha = 100
    params.beta = 0
    params.gamma = 100
    params.bilateral_d = 9
    params.bilateral_sigma_color = 75
    params.bilateral_sigma_space = 75

    # Initial processing
    on_trackbar_change(0)

    print("\nControls:")
    print("- Use sliders to adjust parameters")
    print("- Press 'q' to save and quit")

    while True:
        key = cv2.waitKey(50) & 0xFF  # Increased wait time for better responsiveness
        
        if key == ord('q'):
            # Process one final time with current parameters
            final_processed = process_frame(original_image)
            # Save results
            save_results(args.input_image, final_processed)
            break

    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
