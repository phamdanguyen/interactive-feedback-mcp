#!/usr/bin/env node
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import * as dotenv from 'dotenv';
import {
  extractImageFromFile,
  extractImageFromUrl,
  extractImageFromBase64
} from './image-utils';

dotenv.config();

// Create an MCP server
const server = new McpServer({
  name: "mcp-image-extractor",
  description: "MCP server for analyzing of images from files, URLs, and base64 data for visual content understanding, text extraction (OCR), and object recognition in screenshots and photos",
  version: "1.0.0"
});

// Add extract_image_from_file tool
server.tool(
  "extract_image_from_file",
  {
    file_path: z.string().describe("Path to the image file to analyze (supports screenshots, photos, diagrams, and documents in PNG, JPG, GIF, WebP formats)"),
    resize: z.boolean().default(true).describe("For backward compatibility only. Images are always automatically resized to optimal dimensions (max 512x512) for LLM analysis"),
    max_width: z.number().default(512).describe("For backward compatibility only. Default maximum width is now 512px"),
    max_height: z.number().default(512).describe("For backward compatibility only. Default maximum height is now 512px")
  },
  async (args, extra) => {
    const result = await extractImageFromFile(args);
    return result;
  }
);

// Add extract_image_from_url tool
server.tool(
  "extract_image_from_url",
  {
    url: z.string().describe("URL of the image to analyze for visual content, text extraction, or object recognition (supports web screenshots, photos, diagrams)"),
    resize: z.boolean().default(true).describe("For backward compatibility only. Images are always automatically resized to optimal dimensions (max 512x512) for LLM analysis"),
    max_width: z.number().default(512).describe("For backward compatibility only. Default maximum width is now 512px"),
    max_height: z.number().default(512).describe("For backward compatibility only. Default maximum height is now 512px")
  },
  async (args, extra) => {
    const result = await extractImageFromUrl(args);
    return result;
  }
);

// Add extract_image_from_base64 tool
server.tool(
  "extract_image_from_base64",
  {
    base64: z.string().describe("Base64-encoded image data to analyze (useful for screenshots, images from clipboard, or dynamically generated visuals)"),
    mime_type: z.string().default("image/png").describe("MIME type of the image (e.g., image/png, image/jpeg)"),
    resize: z.boolean().default(true).describe("For backward compatibility only. Images are always automatically resized to optimal dimensions (max 512x512) for LLM analysis"),
    max_width: z.number().default(512).describe("For backward compatibility only. Default maximum width is now 512px"),
    max_height: z.number().default(512).describe("For backward compatibility only. Default maximum height is now 512px")
  },
  async (args, extra) => {
    const result = await extractImageFromBase64(args);
    return result;
  }
);

// Start the server using stdio transport
const transport = new StdioServerTransport();
server.connect(transport).catch((error: unknown) => {
  console.error('Error starting MCP server:', error);
  process.exit(1);
});

console.log('MCP Image Extractor server started in stdio mode'); 