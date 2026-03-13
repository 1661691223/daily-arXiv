/**
 * Trending Keywords Configuration
 * This file contains static configuration for trending data display
 * DO NOT EDIT MANUALLY
 */

const TRENDING_CONFIG = {
    /**
     * Get the URL for trending data JSON file from data branch
     * @returns {string} Full URL to the trending data file
     */
    getDataUrl: function() {
        return DATA_CONFIG.getDataUrl('assets/trending-data.json');
    },
    
    /**
     * LocalStorage key for storing trending panel state
     */
    storageKey: 'arxiv_trending_collapsed'
};
