import { apiClient } from './apiClient';

export interface DashboardData {
  overview: {
    total_content: number;
    published_content: number;
    total_social_posts: number;
    active_platforms: number;
  };
  recent_activity: {
    collection_jobs: Array<{
      id: string;
      status: string;
      created_at: string;
      completed_at?: string;
    }>;
    insights: Array<{
      id: string;
      title: string;
      type: string;
      created_at: string;
    }>;
  };
  service_status: {
    analytics_service: string;
    collection_service: string;
    processing_service: string;
  };
}

export interface ContentAnalyticsData {
  content_id: number;
  report_period: string;
  generated_at: string;
  overall_score: number;
  platform_performance: Record<string, any>;
  insights: Array<{
    id: string;
    insight_type: string;
    metric_category: string;
    title: string;
    description: string;
    value: number | string;
    confidence: number;
    timestamp: string;
  }>;
  recommendations: string[];
  metrics_summary: {
    total_posts: number;
    platforms: string[];
    analysis_period: {
      start: string;
      end: string;
      days: number;
    };
  };
}

export interface ComparisonData {
  comparison_type: string;
  comparison_period: string;
  generated_at: string;
  content_comparison: Array<{
    content_id: number;
    content_title: string;
    overall_score: number;
    platform_performance: Record<string, any>;
    performance_indicators: {
      engagement_rate: number;
      reach_efficiency: number;
      performance_score: number;
    };
    insights: Array<{
      id: string;
      insight_type: string;
      title: string;
      description: string;
      value: number;
      confidence: number;
    }>;
  }>;
  platform_comparison: Array<{
    platform: string;
    total_posts: number;
    average_engagement_rate: number;
    average_reach_efficiency: number;
    average_performance_score: number;
    top_performing_content: Array<{
      content_id: number;
      content_title: string;
      performance_score: number;
    }>;
  }>;
  cross_platform_metrics: {
    best_performing_platform: string;
    worst_performing_platform: string;
    platform_performance_gap: number;
    content_performance_variance: number;
  };
}

export interface TrendData {
  analysis_period: string;
  generated_at: string;
  trend_metrics: {
    engagement_trends: Array<{
      date: string;
      average_engagement_rate: number;
      total_engagement: number;
      content_count: number;
    }>;
    reach_trends: Array<{
      date: string;
      average_reach_efficiency: number;
      total_reach: number;
      content_count: number;
    }>;
    performance_trends: Array<{
      date: string;
      average_performance_score: number;
      top_performing_content: number;
      improvement_rate: number;
    }>;
  };
  platform_trends: Array<{
    platform: string;
    trend_direction: 'increasing' | 'decreasing' | 'stable';
    trend_strength: number;
    key_metrics: {
      engagement_change: number;
      reach_change: number;
      performance_change: number;
    };
    insights: Array<{
      id: string;
      trend_type: string;
      title: string;
      description: string;
      impact: 'positive' | 'negative' | 'neutral';
      confidence: number;
    }>;
  }>;
  content_trends: Array<{
    content_id: number;
    content_title: string;
    trend_performance: {
      start_score: number;
      end_score: number;
      improvement: number;
      trend_direction: 'improving' | 'declining' | 'stable';
    };
    platform_performance: Record<string, {
      trend_direction: 'improving' | 'declining' | 'stable';
      improvement_rate: number;
    }>;
  }>;
  seasonal_patterns: Array<{
    pattern_type: string;
    description: string;
    confidence: number;
    recommendations: string[];
  }>;
}

export interface InsightData {
  generated_at: string;
  analysis_period: string;
  insights: Array<{
    id: string;
    insight_type: 'performance' | 'optimization' | 'trend' | 'opportunity' | 'warning';
    category: 'engagement' | 'reach' | 'content' | 'platform' | 'timing' | 'audience';
    title: string;
    description: string;
    impact: 'high' | 'medium' | 'low';
    confidence: number;
    priority: 'critical' | 'high' | 'medium' | 'low';
    actionable: boolean;
    recommendations: Array<{
      id: string;
      title: string;
      description: string;
      effort: 'low' | 'medium' | 'high';
      expected_impact: 'high' | 'medium' | 'low';
      implementation_steps: string[];
    }>;
    related_metrics: {
      current_value: number;
      benchmark: number;
      improvement_potential: number;
    };
    timestamp: string;
  }>;
  summary: {
    total_insights: number;
    critical_insights: number;
    high_priority_insights: number;
    actionable_insights: number;
    overall_confidence: number;
    improvement_opportunities: number;
  };
  trends: Array<{
    trend_type: string;
    direction: 'positive' | 'negative' | 'neutral';
    strength: number;
    description: string;
    confidence: number;
  }>;
}

export interface CollectionJobStatus {
  job_id: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  progress: number;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  error_message?: string;
  results?: any;
}

export interface ExportOptions {
  format: 'json' | 'csv';
  date_range: {
    start: string;
    end: string;
  };
  platforms?: string[];
  metrics?: string[];
}

class AnalyticsApi {
  private baseUrl = '/api/analytics';

  /**
   * Get dashboard overview data
   */
  async getDashboardData(period: string = '7d', platforms?: string[]): Promise<DashboardData> {
    const params = new URLSearchParams();
    params.append('period', period);
    if (platforms && platforms.length > 0) {
      params.append('platforms', platforms.join(','));
    }

    const response = await apiClient.get(`${this.baseUrl}/dashboard?${params.toString()}`);
    return response.data;
  }

  /**
   * Get analytics for specific content
   */
  async getContentAnalytics(contentId: number, period: string = '7d'): Promise<ContentAnalyticsData> {
    const response = await apiClient.get(`${this.baseUrl}/content/${contentId}?period=${period}`);
    return response.data;
  }

  /**
   * Get content analytics summary
   */
  async getContentSummary(contentId: number, period: string = '7d'): Promise<any> {
    const response = await apiClient.get(`${this.baseUrl}/content/${contentId}/summary?period=${period}`);
    return response.data;
  }

  /**
   * Get content insights
   */
  async getContentInsights(contentId: number, period: string = '7d'): Promise<any> {
    const response = await apiClient.get(`${this.baseUrl}/content/${contentId}/insights?period=${period}`);
    return response.data;
  }

  /**
   * Trigger metrics collection for content
   */
  async collectContentMetrics(contentId: number): Promise<{ job_id: string; status: string }> {
    const response = await apiClient.post(`${this.baseUrl}/content/${contentId}/collect-metrics`);
    return response.data;
  }

  /**
   * Get collection job status
   */
  async getCollectionJobStatus(jobId: string): Promise<CollectionJobStatus> {
    const response = await apiClient.get(`${this.baseUrl}/collection-job/${jobId}`);
    return response.data;
  }

  /**
   * Get performance comparison data
   */
  async getPerformanceComparison(period: string = '7d', platforms?: string[]): Promise<ComparisonData> {
    const params = new URLSearchParams();
    params.append('period', period);
    if (platforms && platforms.length > 0) {
      params.append('platforms', platforms.join(','));
    }

    const response = await apiClient.get(`${this.baseUrl}/comparison?${params.toString()}`);
    return response.data;
  }

  /**
   * Get trend analysis data
   */
  async getTrendAnalysis(period: string = '7d', platforms?: string[]): Promise<TrendData> {
    const params = new URLSearchParams();
    params.append('period', period);
    if (platforms && platforms.length > 0) {
      params.append('platforms', platforms.join(','));
    }

    const response = await apiClient.get(`${this.baseUrl}/trends?${params.toString()}`);
    return response.data;
  }

  /**
   * Export analytics data
   */
  async exportAnalyticsData(options: ExportOptions): Promise<Blob> {
    const response = await apiClient.post(`${this.baseUrl}/export`, options, {
      responseType: 'blob'
    });
    return response.data;
  }

  /**
   * Get analytics service health
   */
  async getServiceHealth(): Promise<any> {
    const response = await apiClient.get(`${this.baseUrl}/health`);
    return response.data;
  }

  /**
   * Cleanup old analytics data
   */
  async cleanupOldData(daysToKeep: number = 90): Promise<{ message: string; deleted_records: number }> {
    const response = await apiClient.post(`${this.baseUrl}/cleanup`, { days_to_keep: daysToKeep });
    return response.data;
  }

  /**
   * Get insights and recommendations
   */
  async getInsights(period: string = '7d', platforms?: string[]): Promise<InsightData> {
    const params = new URLSearchParams();
    params.append('period', period);
    if (platforms && platforms.length > 0) {
      params.append('platforms', platforms.join(','));
    }

    const response = await apiClient.get(`${this.baseUrl}/insights?${params.toString()}`);
    return response.data;
  }

  /**
   * Refresh analytics data
   */
  async refreshAnalytics(platforms?: string[]): Promise<{ message: string; job_ids: string[] }> {
    const payload = platforms && platforms.length > 0 ? { platforms } : {};
    const response = await apiClient.post(`${this.baseUrl}/refresh`, payload);
    return response.data;
  }

  /**
   * Get analytics summary for multiple content pieces
   */
  async getContentAnalyticsBatch(contentIds: number[], period: string = '7d'): Promise<ContentAnalyticsData[]> {
    const params = new URLSearchParams();
    params.append('period', period);
    params.append('content_ids', contentIds.join(','));

    const response = await apiClient.get(`${this.baseUrl}/content/batch?${params.toString()}`);
    return response.data;
  }

  /**
   * Get platform-specific analytics
   */
  async getPlatformAnalytics(platform: string, period: string = '7d'): Promise<any> {
    const response = await apiClient.get(`${this.baseUrl}/platform/${platform}?period=${period}`);
    return response.data;
  }

  /**
   * Get audience insights
   */
  async getAudienceInsights(period: string = '7d', platforms?: string[]): Promise<any> {
    const params = new URLSearchParams();
    params.append('period', period);
    if (platforms && platforms.length > 0) {
      params.append('platforms', platforms.join(','));
    }

    const response = await apiClient.get(`${this.baseUrl}/audience?${params.toString()}`);
    return response.data;
  }

  /**
   * Get competitive analysis
   */
  async getCompetitiveAnalysis(period: string = '7d', competitors?: string[]): Promise<any> {
    const params = new URLSearchParams();
    params.append('period', period);
    if (competitors && competitors.length > 0) {
      params.append('competitors', competitors.join(','));
    }

    const response = await apiClient.get(`${this.baseUrl}/competitive?${params.toString()}`);
    return response.data;
  }

  /**
   * Get predictive analytics
   */
  async getPredictiveAnalytics(period: string = '7d', forecastDays: number = 30): Promise<any> {
    const params = new URLSearchParams();
    params.append('period', period);
    params.append('forecast_days', forecastDays.toString());

    const response = await apiClient.get(`${this.baseUrl}/predictive?${params.toString()}`);
    return response.data;
  }

  /**
   * Get custom report
   */
  async getCustomReport(reportConfig: {
    metrics: string[];
    filters: Record<string, any>;
    group_by?: string[];
    sort_by?: string[];
    limit?: number;
  }): Promise<any> {
    const response = await apiClient.post(`${this.baseUrl}/custom-report`, reportConfig);
    return response.data;
  }

  /**
   * Save custom report configuration
   */
  async saveCustomReport(name: string, config: any): Promise<{ id: string; message: string }> {
    const response = await apiClient.post(`${this.baseUrl}/custom-report/save`, { name, config });
    return response.data;
  }

  /**
   * Get saved custom reports
   */
  async getSavedCustomReports(): Promise<Array<{ id: string; name: string; created_at: string }>> {
    const response = await apiClient.get(`${this.baseUrl}/custom-report/saved`);
    return response.data;
  }

  /**
   * Delete custom report
   */
  async deleteCustomReport(reportId: string): Promise<{ message: string }> {
    const response = await apiClient.delete(`${this.baseUrl}/custom-report/${reportId}`);
    return response.data;
  }

  /**
   * Get analytics alerts
   */
  async getAnalyticsAlerts(): Promise<Array<{
    id: string;
    type: 'threshold' | 'anomaly' | 'trend';
    severity: 'low' | 'medium' | 'high' | 'critical';
    message: string;
    created_at: string;
    acknowledged: boolean;
  }>> {
    const response = await apiClient.get(`${this.baseUrl}/alerts`);
    return response.data;
  }

  /**
   * Acknowledge analytics alert
   */
  async acknowledgeAlert(alertId: string): Promise<{ message: string }> {
    const response = await apiClient.post(`${this.baseUrl}/alerts/${alertId}/acknowledge`);
    return response.data;
  }

  /**
   * Get analytics settings
   */
  async getAnalyticsSettings(): Promise<{
    collection_frequency: number;
    retention_days: number;
    alert_thresholds: Record<string, number>;
    enabled_platforms: string[];
    data_quality_checks: boolean;
  }> {
    const response = await apiClient.get(`${this.baseUrl}/settings`);
    return response.data;
  }

  /**
   * Update analytics settings
   */
  async updateAnalyticsSettings(settings: Partial<{
    collection_frequency: number;
    retention_days: number;
    alert_thresholds: Record<string, number>;
    enabled_platforms: string[];
    data_quality_checks: boolean;
  }>): Promise<{ message: string }> {
    const response = await apiClient.put(`${this.baseUrl}/settings`, settings);
    return response.data;
  }
}

export const analyticsApi = new AnalyticsApi();




