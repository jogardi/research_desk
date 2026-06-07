We have a feature that allows images and figures from the documents to show up directly in search results. 

## Overview

This feature makes images and figures from PDFs searchable and displayable in search results. Users can find images either by their visual content (when descriptions are enabled) or see them alongside text results.

## How It Works

### 1. PDF Processing
When processing PDFs, the Marker service identifies and extracts:
- Figures and images with their bounding boxes
- Associated captions
- Table figures and picture groups

### 2. Image Handling Modes

The system operates in two modes based on the `enable_marker_describe_image` configuration:

#### Description Mode (enable_marker_describe_image = True)
- An LLM generates text descriptions of images
- Descriptions are stored as searchable text (e.g., "This image depicts a medical illustration of a laparoscopic cholecystectomy...")
- Images are extracted from PDF pages using bounding box coordinates
- Both the description and image URL are stored

#### Direct Extraction Mode (enable_marker_describe_image = False)  
- Images are extracted directly from Marker's response as base64-encoded data
- No text descriptions are generated
- Only captions (if present) are searchable

### 3. Storage
Each chunk stores:
- **Text content**: Either the image description or caption
- **Region metadata**: Including the image URL as a data URI (`data:image/jpeg;base64,...`)
- **Position information**: Page number, coordinates, dimensions

### 4. Search Capabilities

#### Semantic Search
- When descriptions are enabled, users can search for image content
- Example: Searching "surgical procedure" finds medical diagrams
- The image descriptions are embedded and indexed like regular text

#### Text Search
- Searches through captions and any text associated with figures
- Does not search image content directly

### 5. Display in UI

The frontend displays images in search results through:
- An `ImageViewer` component that checks for `image_url` in chunk metadata
- Images appear below the associated text in search results
- Images are displayed with responsive sizing

## Configuration

The feature is controlled by settings in `hparams_config.py`:
- `enable_marker_describe_image`: Toggles between description and direct extraction modes
- `marker_endpoint_params`: Controls PDF processing parameters
- `pdf_resolution`: Sets the resolution for image extraction

## Benefits

1. **Enhanced Search**: Users can find images by describing what they're looking for
2. **Visual Context**: Search results include relevant figures and diagrams
3. **Accessibility**: Image descriptions provide text alternatives for visual content
4. **Comprehensive Results**: Both textual and visual information from documents are searchable
