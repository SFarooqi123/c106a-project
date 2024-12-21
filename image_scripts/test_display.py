import cv2
import sys

# Read image path from command line
image_path = sys.argv[1]
print(f"Loading image from: {image_path}")

# Read the image
image = cv2.imread(image_path)
if image is None:
    print("Failed to load image")
    sys.exit(1)

print(f"Image shape: {image.shape}")

# Create window and show image
cv2.namedWindow('Test Image', cv2.WINDOW_NORMAL)
cv2.imshow('Test Image', image)

print("Press any key to exit")
cv2.waitKey(0)
cv2.destroyAllWindows()
