import APIConfigService from '../config/apiConfig';

interface PresentationResult {
  id: string;
  title: string;
  downloadUrl: string;
  status: 'processing' | 'completed' | 'failed';
  slides: number;
  format: string;
}

class SlideSpeakService {
  private config = APIConfigService.getInstance().getPresentationConfig().slideSpeak;
  private endpoint = `${this.config.baseUrl}/presentations`;

  async createPresentation(
    topic: string,
    persona: 'sophia' | 'karen',
    searchData?: any[],
    customContent?: string
  ): Promise<PresentationResult> {
    try {
      const template = this.getPersonaTemplate(persona);
      const enhancedContent = customContent || await this.generateContent(topic, searchData, persona);
      
      const response = await fetch(this.endpoint, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.config.apiKey}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          title: topic,
          template: template,
          content: enhancedContent,
          slides: this.generateSlideOutline(enhancedContent, persona),
          format: 'pptx',
          branding: this.getPersonaBranding(persona),
          options: {
            includeCharts: persona === 'sophia',
            includeReferences: persona === 'karen',
            slideCount: persona === 'sophia' ? 12 : 15
          }
        })
      });

      if (!response.ok) {
        throw new Error(`SlideSpeak API error: ${response.status}`);
      }

      const data = await response.json();
      
      return {
        id: data.id,
        title: topic,
        downloadUrl: data.download_url,
        status: data.status,
        slides: data.slide_count,
        format: 'pptx'
      };
    } catch (error) {
      console.error('SlideSpeak service error:', error);
      throw error;
    }
  }

  private getPersonaTemplate(persona: 'sophia' | 'karen'): string {
    const templates = {
      sophia: 'corporate_business',
      karen: 'scientific_research'
    };
    return templates[persona];
  }

  private getPersonaBranding(persona: 'sophia' | 'karen') {
    const branding = {
      sophia: {
        primaryColor: '#3B82F6',
        secondaryColor: '#60A5FA',
        fontFamily: 'Inter',
        logoPosition: 'top-right'
      },
      karen: {
        primaryColor: '#10B981',
        secondaryColor: '#34D399',
        fontFamily: 'Source Sans Pro',
        logoPosition: 'top-left'
      }
    };
    return branding[persona];
  }

  private async generateContent(topic: string, searchData: any[], persona: string): Promise<string> {
    // This would integrate with Portkey to enhance content
    const baseContent = `
# ${topic}

## Overview
${this.getPersonaIntro(persona, topic)}

## Key Points
${searchData?.slice(0, 5).map(result => `- ${result.title}: ${result.snippet}`).join('\n') || '- Research findings will be populated here'}

## Analysis
${this.getPersonaAnalysis(persona)}

## Recommendations
${this.getPersonaRecommendations(persona)}

## Conclusion
${this.getPersonaConclusion(persona, topic)}
    `;

    return baseContent;
  }

  private getPersonaIntro(persona: string, topic: string): string {
    if (persona === 'sophia') {
      return `This business analysis of ${topic} examines market opportunities, competitive landscape, and strategic recommendations for growth and profitability.`;
    } else {
      return `This research presentation on ${topic} provides a comprehensive review of current literature, methodologies, and clinical implications.`;
    }
  }

  private getPersonaAnalysis(persona: string): string {
    if (persona === 'sophia') {
      return `Market analysis reveals key trends and opportunities. Financial projections indicate potential ROI and growth trajectories.`;
    } else {
      return `Statistical analysis of research data demonstrates significant findings. Methodology review ensures validity and reliability of results.`;
    }
  }

  private getPersonaRecommendations(persona: string): string {
    if (persona === 'sophia') {
      return `Strategic recommendations focus on market entry, competitive positioning, and revenue optimization strategies.`;
    } else {
      return `Clinical recommendations emphasize evidence-based practices, further research needs, and implementation considerations.`;
    }
  }

  private getPersonaConclusion(persona: string, topic: string): string {
    if (persona === 'sophia') {
      return `${topic} presents significant business opportunities with clear pathways to market success and sustainable growth.`;
    } else {
      return `Research on ${topic} contributes valuable insights to the field and establishes foundation for future clinical applications.`;
    }
  }

  private generateSlideOutline(content: string, persona: string) {
    const baseSlides = [
      { title: 'Title Slide', content: 'Introduction and overview' },
      { title: 'Agenda', content: 'Presentation outline' },
      { title: 'Executive Summary', content: 'Key findings and recommendations' }
    ];

    if (persona === 'sophia') {
      return [
        ...baseSlides,
        { title: 'Market Overview', content: 'Industry landscape and trends' },
        { title: 'Competitive Analysis', content: 'Key players and positioning' },
        { title: 'Financial Projections', content: 'Revenue and growth forecasts' },
        { title: 'Strategic Recommendations', content: 'Action items and next steps' },
        { title: 'Implementation Timeline', content: 'Phased approach and milestones' },
        { title: 'Risk Assessment', content: 'Potential challenges and mitigation' },
        { title: 'ROI Analysis', content: 'Return on investment calculations' },
        { title: 'Conclusion', content: 'Summary and call to action' },
        { title: 'Q&A', content: 'Questions and discussion' }
      ];
    } else {
      return [
        ...baseSlides,
        { title: 'Literature Review', content: 'Current research landscape' },
        { title: 'Methodology', content: 'Research design and approach' },
        { title: 'Data Analysis', content: 'Statistical findings and results' },
        { title: 'Clinical Implications', content: 'Practical applications' },
        { title: 'Limitations', content: 'Study constraints and considerations' },
        { title: 'Future Research', content: 'Recommended next steps' },
        { title: 'Regulatory Considerations', content: 'Compliance and approval pathways' },
        { title: 'Implementation Strategy', content: 'Clinical adoption plan' },
        { title: 'References', content: 'Supporting literature and sources' },
        { title: 'Conclusion', content: 'Summary and implications' },
        { title: 'Discussion', content: 'Questions and peer review' }
      ];
    }
  }

  async checkPresentationStatus(presentationId: string): Promise<PresentationResult> {
    try {
      const response = await fetch(`${this.endpoint}/${presentationId}`, {
        headers: {
          'Authorization': `Bearer ${this.config.apiKey}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`SlideSpeak API error: ${response.status}`);
      }

      const data = await response.json();
      
      return {
        id: data.id,
        title: data.title,
        downloadUrl: data.download_url,
        status: data.status,
        slides: data.slide_count,
        format: data.format
      };
    } catch (error) {
      console.error('SlideSpeak status check error:', error);
      throw error;
    }
  }

  async listPresentations(): Promise<PresentationResult[]> {
    try {
      const response = await fetch(this.endpoint, {
        headers: {
          'Authorization': `Bearer ${this.config.apiKey}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`SlideSpeak API error: ${response.status}`);
      }

      const data = await response.json();
      
      return data.presentations?.map((presentation: any) => ({
        id: presentation.id,
        title: presentation.title,
        downloadUrl: presentation.download_url,
        status: presentation.status,
        slides: presentation.slide_count,
        format: presentation.format
      })) || [];
    } catch (error) {
      console.error('SlideSpeak list error:', error);
      return [];
    }
  }
}

export default SlideSpeakService;

