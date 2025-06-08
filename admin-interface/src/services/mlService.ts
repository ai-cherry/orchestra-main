import APIConfigService from '../config/apiConfig';

interface MLModel {
  id: string;
  name: string;
  type: 'classification' | 'regression' | 'clustering' | 'nlp' | 'computer_vision';
  status: 'training' | 'ready' | 'failed' | 'deployed';
  accuracy?: number;
  createdAt: string;
  updatedAt: string;
  metadata: Record<string, any>;
}

interface TrainingJob {
  id: string;
  modelId: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: number;
  metrics: Record<string, number>;
  startedAt: string;
  completedAt?: string;
  logs: string[];
}

interface Prediction {
  id: string;
  modelId: string;
  input: any;
  output: any;
  confidence: number;
  timestamp: string;
}

class MLService {
  private config = APIConfigService.getInstance().getMLConfig();

  async getModels(): Promise<MLModel[]> {
    try {
      const response = await fetch(`${this.config.baseUrl}/models`, {
        headers: {
          'Authorization': `Bearer ${this.config.apiKey}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`ML API error: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      return data.models || [];
    } catch (error) {
      console.error('ML service error:', error);
      throw new Error('Failed to fetch ML models');
    }
  }

  async createModel(name: string, type: MLModel['type'], config: Record<string, any>): Promise<MLModel> {
    try {
      const response = await fetch(`${this.config.baseUrl}/models`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.config.apiKey}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          name,
          type,
          config
        })
      });

      if (!response.ok) {
        throw new Error(`ML API error: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      return data.model;
    } catch (error) {
      console.error('ML create model error:', error);
      throw new Error('Failed to create ML model');
    }
  }

  async trainModel(modelId: string, trainingData: any[], validationData?: any[]): Promise<TrainingJob> {
    try {
      const response = await fetch(`${this.config.baseUrl}/models/${modelId}/train`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.config.apiKey}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          training_data: trainingData,
          validation_data: validationData
        })
      });

      if (!response.ok) {
        throw new Error(`ML API error: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      return data.job;
    } catch (error) {
      console.error('ML train model error:', error);
      throw new Error('Failed to start model training');
    }
  }

  async getTrainingJob(jobId: string): Promise<TrainingJob> {
    try {
      const response = await fetch(`${this.config.baseUrl}/training-jobs/${jobId}`, {
        headers: {
          'Authorization': `Bearer ${this.config.apiKey}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`ML API error: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      return data.job;
    } catch (error) {
      console.error('ML get training job error:', error);
      throw new Error('Failed to fetch training job');
    }
  }

  async predict(modelId: string, input: any): Promise<Prediction> {
    try {
      const response = await fetch(`${this.config.baseUrl}/models/${modelId}/predict`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.config.apiKey}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ input })
      });

      if (!response.ok) {
        throw new Error(`ML API error: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      return {
        id: data.prediction_id,
        modelId,
        input,
        output: data.output,
        confidence: data.confidence,
        timestamp: new Date().toISOString()
      };
    } catch (error) {
      console.error('ML prediction error:', error);
      throw new Error('Failed to make prediction');
    }
  }

  async batchPredict(modelId: string, inputs: any[]): Promise<Prediction[]> {
    try {
      const response = await fetch(`${this.config.baseUrl}/models/${modelId}/batch-predict`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.config.apiKey}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ inputs })
      });

      if (!response.ok) {
        throw new Error(`ML API error: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      return data.predictions.map((pred: any, index: number) => ({
        id: pred.prediction_id,
        modelId,
        input: inputs[index],
        output: pred.output,
        confidence: pred.confidence,
        timestamp: new Date().toISOString()
      }));
    } catch (error) {
      console.error('ML batch prediction error:', error);
      throw new Error('Failed to make batch predictions');
    }
  }

  async deployModel(modelId: string, environment: 'staging' | 'production' = 'staging'): Promise<void> {
    try {
      const response = await fetch(`${this.config.baseUrl}/models/${modelId}/deploy`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.config.apiKey}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ environment })
      });

      if (!response.ok) {
        throw new Error(`ML API error: ${response.status} ${response.statusText}`);
      }
    } catch (error) {
      console.error('ML deploy model error:', error);
      throw new Error('Failed to deploy model');
    }
  }

  async getModelMetrics(modelId: string): Promise<Record<string, number>> {
    try {
      const response = await fetch(`${this.config.baseUrl}/models/${modelId}/metrics`, {
        headers: {
          'Authorization': `Bearer ${this.config.apiKey}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`ML API error: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      return data.metrics;
    } catch (error) {
      console.error('ML get metrics error:', error);
      throw new Error('Failed to fetch model metrics');
    }
  }

  async deleteModel(modelId: string): Promise<void> {
    try {
      const response = await fetch(`${this.config.baseUrl}/models/${modelId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${this.config.apiKey}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`ML API error: ${response.status} ${response.statusText}`);
      }
    } catch (error) {
      console.error('ML delete model error:', error);
      throw new Error('Failed to delete model');
    }
  }

  // Specialized methods for common ML tasks

  async createTextClassificationModel(name: string, labels: string[]): Promise<MLModel> {
    return this.createModel(name, 'nlp', {
      task: 'text_classification',
      labels,
      model_type: 'transformer',
      base_model: 'bert-base-uncased'
    });
  }

  async createImageClassificationModel(name: string, classes: string[]): Promise<MLModel> {
    return this.createModel(name, 'computer_vision', {
      task: 'image_classification',
      classes,
      model_type: 'cnn',
      base_model: 'resnet50'
    });
  }

  async createRegressionModel(name: string, features: string[], target: string): Promise<MLModel> {
    return this.createModel(name, 'regression', {
      task: 'regression',
      features,
      target,
      model_type: 'gradient_boosting'
    });
  }

  async analyzeText(text: string, modelId?: string): Promise<any> {
    // Use default text analysis model if none specified
    const defaultModelId = modelId || 'default-text-analyzer';
    
    return this.predict(defaultModelId, { text });
  }

  async analyzeImage(imageUrl: string, modelId?: string): Promise<any> {
    // Use default image analysis model if none specified
    const defaultModelId = modelId || 'default-image-analyzer';
    
    return this.predict(defaultModelId, { image_url: imageUrl });
  }

  async generateEmbeddings(texts: string[]): Promise<number[][]> {
    try {
      const response = await fetch(`${this.config.baseUrl}/embeddings`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.config.apiKey}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ texts })
      });

      if (!response.ok) {
        throw new Error(`ML API error: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      return data.embeddings;
    } catch (error) {
      console.error('ML embeddings error:', error);
      throw new Error('Failed to generate embeddings');
    }
  }

  async similaritySearch(query: string, documents: string[], topK: number = 5): Promise<Array<{document: string, score: number}>> {
    try {
      const response = await fetch(`${this.config.baseUrl}/similarity-search`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.config.apiKey}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ 
          query, 
          documents, 
          top_k: topK 
        })
      });

      if (!response.ok) {
        throw new Error(`ML API error: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      return data.results;
    } catch (error) {
      console.error('ML similarity search error:', error);
      throw new Error('Failed to perform similarity search');
    }
  }
}

export default MLService;
export type { MLModel, TrainingJob, Prediction };

