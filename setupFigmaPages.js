// setupFigmaPages.js
// Purpose: Creates standard page structure in a Figma file using the REST API.
// Usage:
// 1. Ensure FIGMA_PAT environment variable is set: export FIGMA_PAT='your-token'
// 2. Run: node setupFigmaPages.js

const fetch = require('node-fetch');

// --- FILE_ID set to your Figma project ID ---
const FILE_ID = '368236963';

const FIGMA_PAT = process.env.FIGMA_PAT; // Reads PAT from environment variable

const pagesToCreate = [
  '_Foundations & Variables',
  '_Core Components [Adapted]',
  'Web - Dashboard',
  'Web - Agents',
  'Web - Personas',
  'Web - Memory',
  'Web - Projects',
  'Web - Settings',
  'Web - TrainingGround',
  'Android - Core Screens',
  'Prototypes',
  'Archive'
];

// --- Helper function to create a single page ---
async function createPage(fileId, pageName, accessToken) {
  const apiUrl = `https://api.figma.com/v1/files/${fileId}/pages`;
  console.log(`📄 Attempting to create page: ${pageName}...`);
  try {
    const response = await fetch(apiUrl, {
      method: 'POST',
      headers: {
        'X-Figma-Token': accessToken, // Correct header for PAT
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ name: pageName })
    });

    if (!response.ok) {
      // Log detailed error from Figma API if possible
      let errorDetails = '';
      try {
        const errorJson = await response.json();
        errorDetails = JSON.stringify(errorJson);
      } catch (e) {
        errorDetails = await response.text();
      }
      console.error(`   ❌ Failed: ${response.status} ${response.statusText}. Details: ${errorDetails}`);
      return false; // Indicate failure
    } else {
      // Success
      // const result = await response.json(); // Contains new page node_id if needed
      console.log(`   ✅ Success: Page '${pageName}' created.`);
      return true; // Indicate success
    }
  } catch (error) {
    console.error(`   ❌ Network or script error creating page '${pageName}':`, error);
    return false; // Indicate failure
  }
}

// --- Main execution function ---
async function main() {
  console.log("🚀 Starting Figma page setup script...");

  // Validate prerequisites
  if (!FIGMA_PAT) {
    console.error('❌ Error: FIGMA_PAT environment variable not set.');
    console.error('   Please set it using: export FIGMA_PAT="YOUR_TOKEN"');
    process.exit(1); // Exit if PAT is missing
  }

  console.log(`   Target Figma File ID: ${FILE_ID}`);
  console.log(`   Pages to create: ${pagesToCreate.length}`);

  let successCount = 0;
  let failureCount = 0;

  // Loop through pages and attempt creation
  for (const page of pagesToCreate) {
    const success = await createPage(FILE_ID, page, FIGMA_PAT);
    if (success) {
      successCount++;
    } else {
      failureCount++;
    }
    // Add a small delay to avoid hitting API rate limits aggressively
    await new Promise(resolve => setTimeout(resolve, 250)); // 250ms delay
  }

  console.log('🏁 Page setup script finished.');
  console.log(`   Summary: ${successCount} pages created successfully, ${failureCount} failed.`);

  if (failureCount > 0) {
      console.warn("⚠️ Please review errors above and potentially clean up/re-run if needed.");
  }
}

// --- Run the script ---
main().catch(error => {
  console.error("🚨 Unhandled error during script execution:", error);
  process.exit(1);
});
