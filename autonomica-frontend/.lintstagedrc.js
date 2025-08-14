module.exports = {
  // JavaScript/TypeScript files
  '**/*.{js,jsx,ts,tsx}': [
    'eslint --fix',
    'prettier --write',
    'git add'
  ],

  // CSS/SCSS files
  '**/*.{css,scss}': [
    'stylelint --fix',
    'prettier --write',
    'git add'
  ],

  // JSON, Markdown, and other files
  '**/*.{json,md,yml,yaml}': [
    'prettier --write',
    'git add'
  ],

  // Configuration files
  '**/*.{js,ts}': (filenames) => {
    const configFiles = filenames.filter(filename => 
      filename.includes('config') || 
      filename.includes('eslint') || 
      filename.includes('prettier') ||
      filename.includes('jest') ||
      filename.includes('babel') ||
      filename.includes('webpack') ||
      filename.includes('rollup') ||
      filename.includes('vite')
    );
    
    if (configFiles.length > 0) {
      return [
        'eslint --fix',
        'prettier --write',
        'git add'
      ];
    }
    
    return [];
  }
};