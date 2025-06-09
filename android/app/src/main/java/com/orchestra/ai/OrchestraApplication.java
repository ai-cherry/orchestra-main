package com.orchestra.ai;

import android.app.Application;
import androidx.annotation.NonNull;

/**
 * Main application class for Orchestra AI Android app
 */
public class OrchestraApplication extends Application {
    
    private static OrchestraApplication instance;
    
    @Override
    public void onCreate() {
        super.onCreate();
        instance = this;
        
        // Initialize components
        initializeComponents();
    }
    
    /**
     * Initialize app components and services
     */
    private void initializeComponents() {
        // TODO: Initialize API clients, databases, and services
    }
    
    /**
     * Get application instance
     * @return The singleton application instance
     */
    @NonNull
    public static OrchestraApplication getInstance() {
        return instance;
    }
}
