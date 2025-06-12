package com.orchestra.ai;

import android.content.Context;
import android.content.SharedPreferences;
import android.net.ConnectivityManager;
import android.net.NetworkInfo;
import android.util.Log;

import org.json.JSONException;
import org.json.JSONObject;

import java.io.IOException;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.List;
import java.util.ArrayList;
import java.util.Map;
import java.util.HashMap;

import okhttp3.Call;
import okhttp3.Callback;
import okhttp3.MediaType;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.RequestBody;
import okhttp3.Response;

/**
 * OpenRouter Client for Android
 * Intelligent AI routing with cost optimization and fallbacks
 * 
 * @author Orchestra AI Team
 * @version 1.0.0
 */
public class OpenRouterClient {
    private static final String TAG = "OpenRouterClient";
    private static final String PREFS_NAME = "openrouter_prefs";
    private static final String STATS_KEY = "usage_stats";
    private static final String QUEUE_KEY = "request_queue";
    
    // Configuration
    private static final String BASE_URL_DEV = "http://10.0.2.2:8020"; // Android emulator localhost
    private static final String BASE_URL_PROD = "https://api.orchestra-ai.dev";
    private static final int TIMEOUT_SECONDS = 30;
    private static final int MAX_RETRY_ATTEMPTS = 3;
    private static final int RETRY_DELAY_MS = 1000;
    
    // Use cases
    public enum UseCase {
        CASUAL_CHAT("casual_chat"),
        BUSINESS_ANALYSIS("business_analysis"),
        MEDICAL_COMPLIANCE("medical_compliance"),
        CREATIVE_WRITING("creative_writing"),
        CODE_GENERATION("code_generation"),
        RESEARCH_SEARCH("research_search"),
        STRATEGIC_PLANNING("strategic_planning"),
        QUICK_RESPONSE("quick_response");
        
        private final String value;
        
        UseCase(String value) {
            this.value = value;
        }
        
        public String getValue() {
            return value;
        }
    }
    
    // Personas
    public enum Persona {
        CHERRY("cherry"),
        SOPHIA("sophia"),
        KAREN("karen");
        
        private final String value;
        
        Persona(String value) {
            this.value = value;
        }
        
        public String getValue() {
            return value;
        }
    }
    
    // Complexity levels
    public enum Complexity {
        LOW("low"),
        MEDIUM("medium"),
        HIGH("high");
        
        private final String value;
        
        Complexity(String value) {
            this.value = value;
        }
        
        public String getValue() {
            return value;
        }
    }
    
    // Response callback interface
    public interface ChatCallback {
        void onProgress(String status, String message);
        void onSuccess(ChatResponse response);
        void onError(String error);
    }
    
    // Chat response class
    public static class ChatResponse {
        public final String content;
        public final String provider;
        public final String modelUsed;
        public final int tokensUsed;
        public final double cost;
        public final int responseTimeMs;
        public final boolean fallbackUsed;
        public final String error;
        public final long timestamp;
        
        public ChatResponse(String content, String provider, String modelUsed, 
                          int tokensUsed, double cost, int responseTimeMs, 
                          boolean fallbackUsed, String error) {
            this.content = content;
            this.provider = provider;
            this.modelUsed = modelUsed;
            this.tokensUsed = tokensUsed;
            this.cost = cost;
            this.responseTimeMs = responseTimeMs;
            this.fallbackUsed = fallbackUsed;
            this.error = error;
            this.timestamp = System.currentTimeMillis();
        }
        
        public static ChatResponse fromJson(JSONObject json) throws JSONException {
            return new ChatResponse(
                json.getString("content"),
                json.getString("provider"),
                json.getString("model_used"),
                json.getInt("tokens_used"),
                json.getDouble("cost"),
                json.getInt("response_time_ms"),
                json.optBoolean("fallback_used", false),
                json.optString("error", null)
            );
        }
    }
    
    // Chat request class
    public static class ChatRequest {
        public final Persona persona;
        public final String message;
        public final UseCase useCase;
        public final Complexity complexity;
        public final Integer maxTokens;
        public final Double temperature;
        public final boolean fallbackAllowed;
        
        public ChatRequest(Persona persona, String message, UseCase useCase, 
                         Complexity complexity, Integer maxTokens, Double temperature, 
                         boolean fallbackAllowed) {
            this.persona = persona;
            this.message = message;
            this.useCase = useCase;
            this.complexity = complexity;
            this.maxTokens = maxTokens;
            this.temperature = temperature;
            this.fallbackAllowed = fallbackAllowed;
        }
        
        public JSONObject toJson() throws JSONException {
            JSONObject json = new JSONObject();
            json.put("persona", persona.getValue());
            json.put("message", message);
            json.put("use_case", useCase.getValue());
            json.put("complexity", complexity.getValue());
            if (maxTokens != null) json.put("max_tokens", maxTokens);
            if (temperature != null) json.put("temperature", temperature);
            json.put("fallback_allowed", fallbackAllowed);
            return json;
        }
    }
    
    // Usage statistics class
    public static class UsageStats {
        public int totalRequests = 0;
        public double totalCost = 0.0;
        public double totalSavings = 0.0;
        public Map<String, ProviderStats> providerUsage = new HashMap<>();
        
        public static class ProviderStats {
            public int requests = 0;
            public double totalCost = 0.0;
        }
    }
    
    // Instance variables
    private final Context context;
    private final OkHttpClient httpClient;
    private final SharedPreferences prefs;
    private final ExecutorService executor;
    private final String baseUrl;
    private final UsageStats stats;
    private final List<ChatRequest> requestQueue;
    
    // Singleton instance
    private static OpenRouterClient instance;
    
    public static synchronized OpenRouterClient getInstance(Context context) {
        if (instance == null) {
            instance = new OpenRouterClient(context.getApplicationContext());
        }
        return instance;
    }
    
    private OpenRouterClient(Context context) {
        this.context = context;
        this.prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE);
        this.executor = Executors.newCachedThreadPool();
        this.baseUrl = isDebugBuild() ? BASE_URL_DEV : BASE_URL_PROD;
        this.stats = loadStatsFromPrefs();
        this.requestQueue = new ArrayList<>();
        
        // Configure HTTP client
        this.httpClient = new OkHttpClient.Builder()
            .connectTimeout(TIMEOUT_SECONDS, TimeUnit.SECONDS)
            .readTimeout(TIMEOUT_SECONDS, TimeUnit.SECONDS)
            .writeTimeout(TIMEOUT_SECONDS, TimeUnit.SECONDS)
            .retryOnConnectionFailure(true)
            .build();
        
        Log.i(TAG, "OpenRouterClient initialized with base URL: " + baseUrl);
    }
    
    /**
     * Main chat completion method
     */
    public void chatCompletion(ChatRequest request, ChatCallback callback) {
        if (request.message == null || request.message.trim().isEmpty()) {
            callback.onError("Message cannot be empty");
            return;
        }
        
        if (!isNetworkAvailable()) {
            if (request.fallbackAllowed) {
                queueRequest(request, callback);
                return;
            } else {
                callback.onError("No network connection available");
                return;
            }
        }
        
        executor.execute(() -> {
            try {
                callback.onProgress("connecting", "Connecting to AI service...");
                
                JSONObject requestJson = request.toJson();
                RequestBody body = RequestBody.create(
                    requestJson.toString(),
                    MediaType.get("application/json; charset=utf-8")
                );
                
                Request httpRequest = new Request.Builder()
                    .url(baseUrl + "/chat")
                    .post(body)
                    .addHeader("Content-Type", "application/json")
                    .addHeader("User-Agent", "Orchestra-AI-Android/1.0.0")
                    .build();
                
                callback.onProgress("processing", "Processing request...");
                
                makeRequestWithRetry(httpRequest, new Callback() {
                    @Override
                    public void onFailure(Call call, IOException e) {
                        Log.e(TAG, "Chat completion failed", e);
                        callback.onError("Network error: " + e.getMessage());
                    }
                    
                    @Override
                    public void onResponse(Call call, Response response) throws IOException {
                        try {
                            if (!response.isSuccessful()) {
                                callback.onError("HTTP " + response.code() + ": " + response.message());
                                return;
                            }
                            
                            String responseBody = response.body().string();
                            JSONObject responseJson = new JSONObject(responseBody);
                            
                            ChatResponse chatResponse = ChatResponse.fromJson(responseJson);
                            updateStats(chatResponse);
                            
                            callback.onProgress("complete", "Response received");
                            callback.onSuccess(chatResponse);
                            
                        } catch (JSONException e) {
                            Log.e(TAG, "Failed to parse response", e);
                            callback.onError("Failed to parse response: " + e.getMessage());
                        }
                    }
                });
                
            } catch (JSONException e) {
                Log.e(TAG, "Failed to create request", e);
                callback.onError("Failed to create request: " + e.getMessage());
            }
        });
    }
    
    /**
     * Convenience method for casual chat
     */
    public void casualChat(Persona persona, String message, ChatCallback callback) {
        ChatRequest request = new ChatRequest(
            persona, message, UseCase.CASUAL_CHAT, Complexity.MEDIUM, 
            null, null, true
        );
        chatCompletion(request, callback);
    }
    
    /**
     * Convenience method for business analysis
     */
    public void businessAnalysis(Persona persona, String message, ChatCallback callback) {
        ChatRequest request = new ChatRequest(
            persona, message, UseCase.BUSINESS_ANALYSIS, Complexity.HIGH, 
            null, null, true
        );
        chatCompletion(request, callback);
    }
    
    /**
     * Convenience method for medical compliance
     */
    public void medicalCompliance(Persona persona, String message, ChatCallback callback) {
        ChatRequest request = new ChatRequest(
            persona, message, UseCase.MEDICAL_COMPLIANCE, Complexity.HIGH, 
            null, 0.2, true
        );
        chatCompletion(request, callback);
    }
    
    /**
     * Convenience method for research
     */
    public void research(Persona persona, String message, ChatCallback callback) {
        ChatRequest request = new ChatRequest(
            persona, message, UseCase.RESEARCH_SEARCH, Complexity.MEDIUM, 
            null, null, true
        );
        chatCompletion(request, callback);
    }
    
    /**
     * Convenience method for code generation
     */
    public void codeGeneration(Persona persona, String message, ChatCallback callback) {
        ChatRequest request = new ChatRequest(
            persona, message, UseCase.CODE_GENERATION, Complexity.HIGH, 
            null, 0.1, true
        );
        chatCompletion(request, callback);
    }
    
    /**
     * Get usage statistics
     */
    public CompletableFuture<UsageStats> getStats() {
        CompletableFuture<UsageStats> future = new CompletableFuture<>();
        
        executor.execute(() -> {
            try {
                Request request = new Request.Builder()
                    .url(baseUrl + "/stats")
                    .get()
                    .build();
                
                httpClient.newCall(request).enqueue(new Callback() {
                    @Override
                    public void onFailure(Call call, IOException e) {
                        Log.w(TAG, "Failed to get server stats, returning local stats", e);
                        future.complete(stats);
                    }
                    
                    @Override
                    public void onResponse(Call call, Response response) throws IOException {
                        try {
                            if (response.isSuccessful()) {
                                String responseBody = response.body().string();
                                JSONObject json = new JSONObject(responseBody);
                                
                                // Merge server stats with local stats
                                UsageStats mergedStats = new UsageStats();
                                mergedStats.totalRequests = stats.totalRequests;
                                mergedStats.totalCost = json.optDouble("total_cost", 0.0);
                                mergedStats.totalSavings = json.optDouble("total_savings", 0.0);
                                
                                future.complete(mergedStats);
                            } else {
                                future.complete(stats);
                            }
                        } catch (JSONException e) {
                            Log.w(TAG, "Failed to parse server stats", e);
                            future.complete(stats);
                        }
                    }
                });
                
            } catch (Exception e) {
                Log.e(TAG, "Error getting stats", e);
                future.complete(stats);
            }
        });
        
        return future;
    }
    
    /**
     * Health check
     */
    public CompletableFuture<Boolean> healthCheck() {
        CompletableFuture<Boolean> future = new CompletableFuture<>();
        
        executor.execute(() -> {
            try {
                Request request = new Request.Builder()
                    .url(baseUrl + "/health")
                    .get()
                    .build();
                
                httpClient.newCall(request).enqueue(new Callback() {
                    @Override
                    public void onFailure(Call call, IOException e) {
                        Log.w(TAG, "Health check failed", e);
                        future.complete(false);
                    }
                    
                    @Override
                    public void onResponse(Call call, Response response) throws IOException {
                        future.complete(response.isSuccessful());
                    }
                });
                
            } catch (Exception e) {
                Log.e(TAG, "Error during health check", e);
                future.complete(false);
            }
        });
        
        return future;
    }
    
    /**
     * Queue request for offline processing
     */
    private void queueRequest(ChatRequest request, ChatCallback callback) {
        synchronized (requestQueue) {
            requestQueue.add(request);
            Log.i(TAG, "Request queued for offline processing. Queue size: " + requestQueue.size());
        }
        
        callback.onError("No network connection. Request queued for when connection is restored.");
    }
    
    /**
     * Process queued requests when back online
     */
    public void processQueuedRequests() {
        if (!isNetworkAvailable() || requestQueue.isEmpty()) {
            return;
        }
        
        Log.i(TAG, "Processing " + requestQueue.size() + " queued requests...");
        
        synchronized (requestQueue) {
            List<ChatRequest> toProcess = new ArrayList<>(requestQueue);
            requestQueue.clear();
            
            for (ChatRequest request : toProcess) {
                chatCompletion(request, new ChatCallback() {
                    @Override
                    public void onProgress(String status, String message) {
                        Log.d(TAG, "Queued request progress: " + status + " - " + message);
                    }
                    
                    @Override
                    public void onSuccess(ChatResponse response) {
                        Log.i(TAG, "Queued request completed successfully");
                    }
                    
                    @Override
                    public void onError(String error) {
                        Log.w(TAG, "Queued request failed: " + error);
                    }
                });
            }
        }
    }
    
    /**
     * Make HTTP request with retry logic
     */
    private void makeRequestWithRetry(Request request, Callback callback) {
        makeRequestWithRetry(request, callback, 1);
    }
    
    private void makeRequestWithRetry(Request request, Callback callback, int attempt) {
        httpClient.newCall(request).enqueue(new Callback() {
            @Override
            public void onFailure(Call call, IOException e) {
                if (attempt < MAX_RETRY_ATTEMPTS) {
                    Log.w(TAG, "Request failed (attempt " + attempt + "), retrying...", e);
                    
                    executor.schedule(() -> {
                        makeRequestWithRetry(request, callback, attempt + 1);
                    }, RETRY_DELAY_MS * attempt, TimeUnit.MILLISECONDS);
                } else {
                    Log.e(TAG, "Request failed after " + MAX_RETRY_ATTEMPTS + " attempts", e);
                    callback.onFailure(call, e);
                }
            }
            
            @Override
            public void onResponse(Call call, Response response) throws IOException {
                callback.onResponse(call, response);
            }
        });
    }
    
    /**
     * Check network availability
     */
    private boolean isNetworkAvailable() {
        ConnectivityManager connectivityManager = 
            (ConnectivityManager) context.getSystemService(Context.CONNECTIVITY_SERVICE);
        
        if (connectivityManager != null) {
            NetworkInfo activeNetworkInfo = connectivityManager.getActiveNetworkInfo();
            return activeNetworkInfo != null && activeNetworkInfo.isConnected();
        }
        
        return false;
    }
    
    /**
     * Check if this is a debug build
     */
    private boolean isDebugBuild() {
        return BuildConfig.DEBUG;
    }
    
    /**
     * Update usage statistics
     */
    private void updateStats(ChatResponse response) {
        stats.totalRequests++;
        stats.totalCost += response.cost;
        
        if (!stats.providerUsage.containsKey(response.provider)) {
            stats.providerUsage.put(response.provider, new UsageStats.ProviderStats());
        }
        
        UsageStats.ProviderStats providerStats = stats.providerUsage.get(response.provider);
        providerStats.requests++;
        providerStats.totalCost += response.cost;
        
        saveStatsToPrefs();
    }
    
    /**
     * Load statistics from SharedPreferences
     */
    private UsageStats loadStatsFromPrefs() {
        UsageStats loadedStats = new UsageStats();
        
        try {
            String statsJson = prefs.getString(STATS_KEY, null);
            if (statsJson != null) {
                JSONObject json = new JSONObject(statsJson);
                loadedStats.totalRequests = json.optInt("totalRequests", 0);
                loadedStats.totalCost = json.optDouble("totalCost", 0.0);
                loadedStats.totalSavings = json.optDouble("totalSavings", 0.0);
                
                // Load provider usage
                JSONObject providerUsageJson = json.optJSONObject("providerUsage");
                if (providerUsageJson != null) {
                    for (String provider : providerUsageJson.keys()) {
                        JSONObject providerJson = providerUsageJson.getJSONObject(provider);
                        UsageStats.ProviderStats providerStats = new UsageStats.ProviderStats();
                        providerStats.requests = providerJson.optInt("requests", 0);
                        providerStats.totalCost = providerJson.optDouble("totalCost", 0.0);
                        loadedStats.providerUsage.put(provider, providerStats);
                    }
                }
            }
        } catch (JSONException e) {
            Log.w(TAG, "Failed to load stats from preferences", e);
        }
        
        return loadedStats;
    }
    
    /**
     * Save statistics to SharedPreferences
     */
    private void saveStatsToPrefs() {
        try {
            JSONObject json = new JSONObject();
            json.put("totalRequests", stats.totalRequests);
            json.put("totalCost", stats.totalCost);
            json.put("totalSavings", stats.totalSavings);
            
            JSONObject providerUsageJson = new JSONObject();
            for (Map.Entry<String, UsageStats.ProviderStats> entry : stats.providerUsage.entrySet()) {
                JSONObject providerJson = new JSONObject();
                providerJson.put("requests", entry.getValue().requests);
                providerJson.put("totalCost", entry.getValue().totalCost);
                providerUsageJson.put(entry.getKey(), providerJson);
            }
            json.put("providerUsage", providerUsageJson);
            
            prefs.edit().putString(STATS_KEY, json.toString()).apply();
            
        } catch (JSONException e) {
            Log.w(TAG, "Failed to save stats to preferences", e);
        }
    }
    
    /**
     * Clear all statistics
     */
    public void clearStats() {
        stats.totalRequests = 0;
        stats.totalCost = 0.0;
        stats.totalSavings = 0.0;
        stats.providerUsage.clear();
        
        prefs.edit().remove(STATS_KEY).apply();
        Log.i(TAG, "Statistics cleared");
    }
    
    /**
     * Get persona recommendations
     */
    public static class PersonaRecommendation {
        public final List<UseCase> preferredUseCases;
        public final Complexity defaultComplexity;
        public final Double defaultTemperature;
        public final String description;
        
        public PersonaRecommendation(List<UseCase> preferredUseCases, 
                                   Complexity defaultComplexity, 
                                   Double defaultTemperature, 
                                   String description) {
            this.preferredUseCases = preferredUseCases;
            this.defaultComplexity = defaultComplexity;
            this.defaultTemperature = defaultTemperature;
            this.description = description;
        }
    }
    
    public PersonaRecommendation getPersonaRecommendation(Persona persona) {
        switch (persona) {
            case CHERRY:
                return new PersonaRecommendation(
                    List.of(UseCase.CASUAL_CHAT, UseCase.CREATIVE_WRITING, UseCase.QUICK_RESPONSE),
                    Complexity.MEDIUM,
                    0.7,
                    "Cherry is great for casual conversations, creative tasks, and quick responses."
                );
            case SOPHIA:
                return new PersonaRecommendation(
                    List.of(UseCase.BUSINESS_ANALYSIS, UseCase.STRATEGIC_PLANNING, UseCase.RESEARCH_SEARCH),
                    Complexity.HIGH,
                    0.3,
                    "Sophia excels at business analysis, strategic planning, and research."
                );
            case KAREN:
                return new PersonaRecommendation(
                    List.of(UseCase.MEDICAL_COMPLIANCE, UseCase.BUSINESS_ANALYSIS, UseCase.RESEARCH_SEARCH),
                    Complexity.HIGH,
                    0.2,
                    "Karen specializes in medical compliance, healthcare analysis, and research."
                );
            default:
                return getPersonaRecommendation(Persona.CHERRY);
        }
    }
} 