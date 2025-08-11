// Dashboard Configuration
export const DASHBOARD_CONFIG = {
  // Grafana Dashboard URLs
  grafana: {
    baseUrl: 'http://localhost:3000',
    comprehensiveDashboard: 'http://localhost:3000/d/d323749f-135e-455a-aa74-4915a52ef0b9/websocket-service-comprehensive-dashboard',
    dashboardUid: 'd323749f-135e-455a-aa74-4915a52ef0b9',
    dashboardSlug: 'websocket-service-comprehensive-dashboard'
  },
  
  // Prometheus URLs
  prometheus: {
    baseUrl: 'http://localhost:9090',
    targets: 'http://localhost:9090/targets',
    graph: 'http://localhost:9090/graph'
  },
  
  // Application URLs
  app: {
    metrics: '/metrics',
    healthz: '/healthz',
    readyz: '/readyz'
  }
};

// Helper function to get dashboard URL
export const getDashboardUrl = (type: 'grafana' | 'prometheus' = 'grafana') => {
  switch (type) {
    case 'grafana':
      return DASHBOARD_CONFIG.grafana.comprehensiveDashboard;
    case 'prometheus':
      return DASHBOARD_CONFIG.prometheus.baseUrl;
    default:
      return DASHBOARD_CONFIG.grafana.comprehensiveDashboard;
  }
};

// Helper function to get Grafana base URL
export const getGrafanaBaseUrl = () => DASHBOARD_CONFIG.grafana.baseUrl;

// Helper function to get Prometheus base URL
export const getPrometheusBaseUrl = () => DASHBOARD_CONFIG.prometheus.baseUrl;
