import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async redirects() {
    return [
      { source: "/coordination", destination: "/app-backend", permanent: false },
      { source: "/coordinations", destination: "/app-backend", permanent: false },
      { source: "/dashboard/coordination", destination: "/app-backend", permanent: false },
      { source: "/dashboard/coordinations", destination: "/app-backend", permanent: false },
      { source: "/dashboard/requests", destination: "/app-backend/requests", permanent: false },
      { source: "/dashboard/requests/:path*", destination: "/app-backend/requests/:path*", permanent: false },
      { source: "/dashboard/volunteers", destination: "/app-backend/volunteers", permanent: false },
      { source: "/dashboard/volunteers/:path*", destination: "/app-backend/volunteers/:path*", permanent: false },
      { source: "/dashboard/assignments", destination: "/app-backend/assignments", permanent: false },
      { source: "/dashboard/assignments/:path*", destination: "/app-backend/assignments/:path*", permanent: false },
      { source: "/dashboard/resources", destination: "/app-backend/resources", permanent: false },
      { source: "/dashboard/resources/:path*", destination: "/app-backend/resources/:path*", permanent: false },
      { source: "/dashboard/shelters", destination: "/app-backend/shelters", permanent: false },
      { source: "/dashboard/shelters/:path*", destination: "/app-backend/shelters/:path*", permanent: false },
      { source: "/dashboard/alerts", destination: "/app-backend/alerts", permanent: false },
      { source: "/dashboard/alerts/:path*", destination: "/app-backend/alerts/:path*", permanent: false },
      { source: "/dashboard/audit", destination: "/app-backend/audit", permanent: false },
      { source: "/dashboard/audit/:path*", destination: "/app-backend/audit/:path*", permanent: false },
      { source: "/risk-map", destination: "/dashboard", permanent: false },
      { source: "/analytics", destination: "/dashboard", permanent: false },
      { source: "/prediction", destination: "/dashboard", permanent: false },
      { source: "/alerts", destination: "/app-backend/alerts", permanent: false },
      { source: "/alerts/:path*", destination: "/app-backend/alerts/:path*", permanent: false },
      { source: "/admin", destination: "/dashboard", permanent: false },
      { source: "/insights", destination: "/dashboard", permanent: false },
      { source: "/insights/:path*", destination: "/dashboard", permanent: false },
    ];
  },
};

export default nextConfig;
