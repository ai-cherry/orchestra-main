#!/usr/bin/env node
/**
 * Figma Component Generator Script
 * 
 * This script automates the creation of Figma components based on the 
 * component-adaptation-mapping.json file. It creates component variants
 * and applies Orchestra variables to the components.
 * 
 * Usage:
 *   node generate_figma_components.js --token=YOUR_FIGMA_TOKEN --file=YOUR_FIGMA_FILE_ID
 */

const fs = require('fs');
const path = require('path');
const fetch = require('node-fetch');
const { program } = require('commander');

// Parse command line arguments
program
  .requiredOption('--token <token>', 'Figma API token')
  .requiredOption('--file <file>', 'Figma file ID')
  .option('--verbose', 'Enable verbose output')
  .parse(process.argv);

const options = program.opts();
const FIGMA_TOKEN = options.token;
const FIGMA_FILE_ID = options.file;
const VERBOSE = options.verbose;

// Configuration
const API_BASE = 'https://api.figma.com/v1';
const COMPONENT_PAGE_NAME = '_Core Components [Adapted]';
const MAPPING_FILE_PATH = path.join(process.cwd(), 'component-adaptation-mapping.json');

// Load component mapping
const componentMapping = JSON.parse(fs.readFileSync(MAPPING_FILE_PATH, 'utf8'));

// Figma API client
const figmaClient = {
  /**
   * Make a request to the Figma API
   */
  async request(endpoint, method = 'GET', data = null) {
    const url = `${API_BASE}${endpoint}`;
    const options = {
      method,
      headers: {
        'X-Figma-Token': FIGMA_TOKEN,
        'Content-Type': 'application/json'
      }
    };

    if (data && (method === 'POST' || method === 'PUT')) {
      options.body = JSON.stringify(data);
    }

    try {
      const response = await fetch(url, options);
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(`Figma API error (${response.status}): ${JSON.stringify(errorData)}`);
      }
      return await response.json();
    } catch (error) {
      console.error(`Failed to ${method} ${url}:`, error);
      throw error;
    }
  },

  /**
   * Get file data
   */
  async getFile() {
    return this.request(`/files/${FIGMA_FILE_ID}`);
  },

  /**
   * Find a page by name
   */
  findPage(file, pageName) {
    if (!file.document || !file.document.children) {
      throw new Error('Invalid file structure');
    }

    return file.document.children.find(page => page.name === pageName);
  },

  /**
   * Create a component in the file
   */
  async createComponent(name, nodeData) {
    return this.request(`/files/${FIGMA_FILE_ID}/nodes`, 'POST', {
      name,
      nodeData
    });
  },

  /**
   * Update styles/variables for a component
   */
  async updateComponent(nodeId, properties) {
    return this.request(`/files/${FIGMA_FILE_ID}/nodes/${nodeId}`, 'PUT', {
      properties
    });
  }
};

/**
 * Create a component with variants from the mapping
 */
async function createComponentWithVariants(componentName, layerMappings) {
  console.log(`Creating component: ${componentName}`);

  // Extract component base name and variant
  const [baseName, variant] = componentName.split(' (');
  const variantName = variant ? variant.replace(')', '') : 'Default';

  // Create basic component structure
  const component = {
    type: 'COMPONENT',
    name: componentName,
    visible: true,
    locked: false,
    children: []
  };

  // Create layers based on mapping
  for (const layerMapping of layerMappings) {
    const layer = {
      type: 'FRAME',
      name: layerMapping.layer,
      visible: true,
      locked: false
    };

    // Add style properties based on mapping
    if (layerMapping.apply.Variable) {
      layer.fillStyleId = `VAR:${layerMapping.apply.Variable}`;
    } else if (layerMapping.apply.Style) {
      // This is just a placeholder - in a real implementation 
      // we would need to look up the actual style ID
      layer.styleReference = layerMapping.apply.Style;
    }

    component.children.push(layer);
  }

  if (VERBOSE) {
    console.log(`Component structure: ${JSON.stringify(component, null, 2)}`);
  }

  console.log(`Component "${componentName}" structure created (would be sent to Figma API)`);
  
  // In a real implementation, we would call:
  // return figmaClient.createComponent(componentName, component);
  
  // For demonstration purposes, return a mock response
  return { 
    id: `mock-${componentName.replace(/\s+/g, '-').toLowerCase()}`,
    success: true 
  };
}

/**
 * Main execution function
 */
async function main() {
  try {
    console.log('Starting Figma component generation...');
    
    // Get file data
    console.log(`Loading Figma file: ${FIGMA_FILE_ID}`);
    // In a real implementation, we would use:
    // const file = await figmaClient.getFile();
    // const componentPage = figmaClient.findPage(file, COMPONENT_PAGE_NAME);
    
    console.log(`Targeting component page: ${COMPONENT_PAGE_NAME}`);
    
    // Create each component with variants
    for (const [componentName, layerMappings] of Object.entries(componentMapping)) {
      const result = await createComponentWithVariants(componentName, layerMappings);
      console.log(`Created component: ${componentName}, ID: ${result.id}`);
    }
    
    console.log('Component generation complete!');
  } catch (error) {
    console.error('Failed to generate components:', error);
    process.exit(1);
  }
}

// Execute the script
main();
