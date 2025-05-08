from pdf2image import convert_from_path

# Path to the PDF file
pdf_path = 'example.pdf'

# Convert PDF to a list of images
# By default, Poppler installed via Homebrew is in /usr/local/bin
images = convert_from_path(pdf_path, dpi=300)

# Save each page as an image
for i, image in enumerate(images):
    output_path = f'page_{i + 1}.jpg'
    image.save(output_path, 'JPEG')
    print(f'Saved: {output_path}')

print("PDF successfully converted to images.")
