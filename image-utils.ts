import axios from 'axios';
import sharp from 'sharp';
import * as fs from 'fs';
import * as path from 'path';

// Configuration
const MAX_IMAGE_SIZE = parseInt(process.env.MAX_IMAGE_SIZE || '10485760', 10); // 10MB default
const ALLOWED_DOMAINS = process.env.ALLOWED_DOMAINS ? process.env.ALLOWED_DOMAINS.split(',') : [];

// Default max dimensions for optimal LLM context usage
const DEFAULT_MAX_WIDTH = 512;
const DEFAULT_MAX_HEIGHT = 512;

// Compression configuration based on format - new addition
type SupportedFormat = 'jpeg' | 'jpg' | 'png' | 'webp' | 'gif' | 'svg' | 'avif' | 'tiff';

const COMPRESSION_OPTIONS: Record<SupportedFormat, object> = {
  jpeg: { quality: 80 },
  jpg: { quality: 80 },
  png: { quality: 80, compressionLevel: 9 },
  webp: { quality: 80 },
  gif: { },
  svg: { },
  avif: { quality: 80 },
  tiff: { quality: 80 }
};

// Type definitions
export type ExtractImageFromFileParams = {
  file_path: string;
  resize: boolean;
  max_width: number;
  max_height: number;
};

export type ExtractImageFromUrlParams = {
  url: string;
  resize: boolean;
  max_width: number;
  max_height: number;
};

export type ExtractImageFromBase64Params = {
  base64: string;
  mime_type: string;
  resize: boolean;
  max_width: number;
  max_height: number;
};

// MCP SDK expects this specific format for tool responses
export type McpToolResponse = {
  [x: string]: unknown;
  content: (
    | { [x: string]: unknown; type: "text"; text: string; }
    | { [x: string]: unknown; type: "image"; data: string; mimeType: string; }
    | { 
        [x: string]: unknown; 
        type: "resource"; 
        resource: { 
          [x: string]: unknown; 
          text: string; 
          uri: string; 
          mimeType?: string; 
        } | { 
          [x: string]: unknown; 
          uri: string; 
          blob: string; 
          mimeType?: string; 
        }; 
      }
  )[];
  _meta?: Record<string, unknown>;
  isError?: boolean;
};

// Helper function to compress image based on format
async function compressImage(imageBuffer: Buffer, formatStr: string): Promise<Buffer> {
  const sharpInstance = sharp(imageBuffer);
  const format = formatStr.toLowerCase() as SupportedFormat;
  
  // Check if format is supported
  if (format in COMPRESSION_OPTIONS) {
    const options = COMPRESSION_OPTIONS[format];
    
    // Use specific methods based on format
    switch (format) {
      case 'jpeg':
      case 'jpg':
        return await sharpInstance.jpeg(options as any).toBuffer();
      case 'png':
        return await sharpInstance.png(options as any).toBuffer();
      case 'webp':
        return await sharpInstance.webp(options as any).toBuffer();
      case 'avif':
        return await sharpInstance.avif(options as any).toBuffer();
      case 'tiff':
        return await sharpInstance.tiff(options as any).toBuffer();
      // For formats without specific compression options
      case 'gif':
      case 'svg':
        return await sharpInstance.toBuffer();
    }
  }
  
  // Default to jpeg if format not supported
  return await sharpInstance.jpeg(COMPRESSION_OPTIONS.jpeg as any).toBuffer();
}

// Extract image from file
export async function extractImageFromFile(params: ExtractImageFromFileParams): Promise<McpToolResponse> {
  try {
    const { file_path, resize, max_width, max_height } = params;
    
    // Check if file exists
    if (!fs.existsSync(file_path)) {
      return {
        content: [{ type: "text", text: `Error: File ${file_path} does not exist` }],
        isError: true
      };
    }
    
    // Read file
    let imageBuffer = fs.readFileSync(file_path);
    
    // Check size
    if (imageBuffer.length > MAX_IMAGE_SIZE) {
      return {
        content: [{ type: "text", text: `Error: Image size exceeds maximum allowed size of ${MAX_IMAGE_SIZE} bytes` }],
        isError: true
      };
    }
    
    // Process the image
    let metadata = await sharp(imageBuffer).metadata();
    
    // Always resize to ensure the base64 representation is reasonable
    // This will help avoid consuming too much of the context window
    if (metadata.width && metadata.height) {
      // Use provided dimensions or fallback to defaults for optimal LLM context usage
      const targetWidth = Math.min(metadata.width, DEFAULT_MAX_WIDTH);
      const targetHeight = Math.min(metadata.height, DEFAULT_MAX_HEIGHT);
      
      // Only resize if needed
      if (metadata.width > targetWidth || metadata.height > targetHeight) {
        imageBuffer = await sharp(imageBuffer)
          .resize({
            width: targetWidth,
            height: targetHeight,
            fit: 'inside',
            withoutEnlargement: true
          })
          .toBuffer();
        
        // Update metadata after resize
        metadata = await sharp(imageBuffer).metadata();
      }
    }

    // Determine mime type based on file extension
    const fileExt = path.extname(file_path).toLowerCase();
    let mimeType = 'image/jpeg';
    let format = 'jpeg';
    
    if (fileExt === '.png') {
      mimeType = 'image/png';
      format = 'png';
    }
    else if (fileExt === '.jpg' || fileExt === '.jpeg') {
      mimeType = 'image/jpeg';
      format = 'jpeg';
    }
    else if (fileExt === '.gif') {
      mimeType = 'image/gif';
      format = 'gif';
    }
    else if (fileExt === '.webp') {
      mimeType = 'image/webp';
      format = 'webp';
    }
    else if (fileExt === '.svg') {
      mimeType = 'image/svg+xml';
      format = 'svg';
    }
    else if (fileExt === '.avif') {
      mimeType = 'image/avif';
      format = 'avif';
    }
    
    // Compress the image based on its format
    try {
      imageBuffer = await compressImage(imageBuffer, format);
    } catch (compressionError) {
      console.warn('Compression warning, using original image:', compressionError);
      // Continue with the original image if compression fails
    }
    
    // Convert to base64
    const base64 = imageBuffer.toString('base64');

    // Return both text and image content
    return {
      content: [
        { 
          type: "text", 
          text: JSON.stringify({
            width: metadata.width,
            height: metadata.height,
            format: metadata.format,
            size: imageBuffer.length
          })
        },
        {
          type: "image",
          data: base64,
          mimeType: mimeType
        }
      ]
    };
  } catch (error: unknown) {
    console.error('Error processing image file:', error);
    return {
      content: [{ type: "text", text: `Error: ${error instanceof Error ? error.message : String(error)}` }],
      isError: true
    };
  }
}

// Extract image from URL
export async function extractImageFromUrl(params: ExtractImageFromUrlParams): Promise<McpToolResponse> {
  try {
    const { url, resize, max_width, max_height } = params;
    
    // Validate URL
    if (!url.startsWith('http://') && !url.startsWith('https://')) {
      return {
        content: [{ type: "text", text: "Error: URL must start with http:// or https://" }],
        isError: true
      };
    }

    // Domain validation if ALLOWED_DOMAINS is set
    if (ALLOWED_DOMAINS.length > 0) {
      const urlObj = new URL(url);
      const domain = urlObj.hostname;
      const isAllowed = ALLOWED_DOMAINS.some((allowedDomain: string) => 
        domain === allowedDomain || domain.endsWith(`.${allowedDomain}`)
      );

      if (!isAllowed) {
        return {
          content: [{ type: "text", text: `Error: Domain ${domain} is not in the allowed domains list` }],
          isError: true
        };
      }
    }

    // Fetch the image
    const response = await axios.get(url, {
      responseType: 'arraybuffer',
      maxContentLength: MAX_IMAGE_SIZE,
    });

    // Process the image
    let imageBuffer = Buffer.from(response.data);
    let metadata = await sharp(imageBuffer).metadata();
    
    // Always resize to ensure the base64 representation is reasonable
    // This will help avoid consuming too much of the context window
    if (metadata.width && metadata.height) {
      // Use provided dimensions or fallback to defaults for optimal LLM context usage
      const targetWidth = Math.min(metadata.width, DEFAULT_MAX_WIDTH);
      const targetHeight = Math.min(metadata.height, DEFAULT_MAX_HEIGHT);
      
      // Only resize if needed
      if (metadata.width > targetWidth || metadata.height > targetHeight) {
        imageBuffer = await sharp(imageBuffer)
          .resize({
            width: targetWidth,
            height: targetHeight,
            fit: 'inside',
            withoutEnlargement: true
          })
          .toBuffer();
        
        // Update metadata after resize
        metadata = await sharp(imageBuffer).metadata();
      }
    }

    // Compress the image based on its format
    try {
      const format = metadata.format || 'jpeg';
      imageBuffer = await compressImage(imageBuffer, format);
    } catch (compressionError) {
      console.warn('Compression warning, using original image:', compressionError);
      // Continue with the original image if compression fails
    }

    // Convert to base64
    const base64 = imageBuffer.toString('base64');
    const mimeType = response.headers['content-type'] || 'image/jpeg';

    // Return both text and image content
    return {
      content: [
        { 
          type: "text", 
          text: JSON.stringify({
            width: metadata.width,
            height: metadata.height,
            format: metadata.format,
            size: imageBuffer.length
          })
        },
        {
          type: "image",
          data: base64,
          mimeType: mimeType
        }
      ]
    };
  } catch (error: unknown) {
    console.error('Error processing image from URL:', error);
    return {
      content: [{ type: "text", text: `Error: ${error instanceof Error ? error.message : String(error)}` }],
      isError: true
    };
  }
}

// Extract image from base64
export async function extractImageFromBase64(params: ExtractImageFromBase64Params): Promise<McpToolResponse> {
  try {
    const { base64, mime_type, resize, max_width, max_height } = params;
    
    // Decode base64
    let imageBuffer;
    try {
      imageBuffer = Buffer.from(base64, 'base64');
      
      // Quick validation - valid base64 strings should be decodable
      if (imageBuffer.length === 0) {
        throw new Error("Invalid base64 string - decoded to empty buffer");
      }
    } catch (e) {
      return {
        content: [{ type: "text", text: `Error: Invalid base64 string - ${e instanceof Error ? e.message : String(e)}` }],
        isError: true
      };
    }
    
    // Check size
    if (imageBuffer.length > MAX_IMAGE_SIZE) {
      return {
        content: [{ type: "text", text: `Error: Image size exceeds maximum allowed size of ${MAX_IMAGE_SIZE} bytes` }],
        isError: true
      };
    }
    
    // Process the image
    let metadata;
    try {
      metadata = await sharp(imageBuffer).metadata();
    } catch (e) {
      return {
        content: [{ type: "text", text: `Error: Could not process image data - ${e instanceof Error ? e.message : String(e)}` }],
        isError: true
      };
    }
    
    // Always resize to ensure the base64 representation is reasonable
    // This will help avoid consuming too much of the context window
    if (metadata.width && metadata.height) {
      // Use provided dimensions or fallback to defaults for optimal LLM context usage
      const targetWidth = Math.min(metadata.width, DEFAULT_MAX_WIDTH);
      const targetHeight = Math.min(metadata.height, DEFAULT_MAX_HEIGHT);
      
      // Only resize if needed
      if (metadata.width > targetWidth || metadata.height > targetHeight) {
        imageBuffer = await sharp(imageBuffer)
          .resize({
            width: targetWidth,
            height: targetHeight,
            fit: 'inside',
            withoutEnlargement: true
          })
          .toBuffer();
        
        // Update metadata after resize
        metadata = await sharp(imageBuffer).metadata();
      }
    }

    // Compress the image based on its format
    try {
      const format = metadata.format || mime_type.split('/')[1] || 'jpeg';
      imageBuffer = await compressImage(imageBuffer, format);
    } catch (compressionError) {
      console.warn('Compression warning, using original image:', compressionError);
      // Continue with the original image if compression fails
    }

    // Convert back to base64
    const processedBase64 = imageBuffer.toString('base64');

    // Return both text and image content
    return {
      content: [
        { 
          type: "text", 
          text: JSON.stringify({
            width: metadata.width,
            height: metadata.height,
            format: metadata.format,
            size: imageBuffer.length
          })
        },
        {
          type: "image",
          data: processedBase64,
          mimeType: mime_type
        }
      ]
    };
  } catch (error: unknown) {
    console.error('Error processing base64 image:', error);
    return {
      content: [{ type: "text", text: `Error: ${error instanceof Error ? error.message : String(error)}` }],
      isError: true
    };
  }
} 