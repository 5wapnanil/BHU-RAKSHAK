export interface ArticleSection {
  heading: string;
  content: string[];
}

export interface Article {
  id: string;
  slug: string;
  category: string;
  title: string;
  excerpt: string;
  readTime: string;
  featured: boolean;
  publishedAt: string;
  author: string;
  content: ArticleSection[];
}

export const ARTICLES: Article[] = [
  {
    id: "1",
    slug: "why-do-landslides-happen",
    category: "LANDSLIDE SCIENCE",
    title: "Why Do Landslides Happen? Understanding the Signals Before Failure",
    excerpt: "Landslides are triggered by a combination of geological, environmental, and human factors. Understanding these signals is the first step toward risk assessment.",
    readTime: "6 min read",
    featured: true,
    publishedAt: "2026-08-15",
    author: "LRM Research Team",
    content: [
      {
        heading: "What Causes Landslides?",
        content: [
          "Landslides occur when the forces driving slope movement exceed the forces resisting it. This imbalance can be triggered by a variety of natural and anthropogenic factors, and understanding these mechanisms is fundamental to landslide risk assessment.",
          "Slope instability is influenced by gravity, the internal strength of soil and rock, and the geometry of the terrain. When external conditions change — such as during heavy rainfall or seismic activity — the equilibrium of a slope can be disrupted."
        ]
      },
      {
        heading: "The Role of Rainfall and Soil Moisture",
        content: [
          "Rainfall is one of the most common triggers of landslides, particularly in regions with steep terrain and saturated soils. When rain infiltrates the ground, it increases pore-water pressure within the soil matrix, reducing the effective stress that holds the slope together.",
          "Cumulative rainfall over several days can saturate soil layers gradually, while intense short-duration rainfall can cause rapid increases in pore-water pressure. Both patterns can contribute to slope failure, and monitoring these variables provides measurable indicators of changing landslide susceptibility."
        ]
      },
      {
        heading: "Terrain, Geology, and Vegetation",
        content: [
          "The physical characteristics of a slope — including its angle, aspect, elevation, and geological composition — play a significant role in determining landslide susceptibility. Steeper slopes with weaker geological materials are generally more prone to failure.",
          "Vegetation contributes to slope stability through root reinforcement and moisture regulation. Deforestation or land-use changes can remove this natural reinforcement, increasing the likelihood of slope movement in vulnerable areas."
        ]
      },
      {
        heading: "Environmental Indicators for Risk Assessment",
        content: [
          "Modern landslide risk assessment relies on measuring environmental variables that can indicate changing slope conditions. These include soil moisture levels, rainfall accumulation, slope angle, elevation, vegetation indices (such as NDVI), and terrain characteristics.",
          "By monitoring these indicators over time, it becomes possible to identify areas where the risk of landslide activity may be increasing. While no single variable can perfectly predict every landslide, the combination of multiple environmental signals provides a scientifically grounded approach to assessing potential risk."
        ]
      }
    ]
  },
  {
    id: "2",
    slug: "gis-landslide-risk-maps",
    category: "GIS & REMOTE SENSING",
    title: "How GIS Turns Terrain Data into Landslide Risk Maps",
    excerpt: "Geographic Information Systems combine elevation, slope, land use, soil characteristics, and historical landslide data to produce spatial risk assessments.",
    readTime: "7 min read",
    featured: true,
    publishedAt: "2026-08-20",
    author: "LRM Research Team",
    content: [
      {
        heading: "The Role of GIS in Landslide Assessment",
        content: [
          "Geographic Information Systems (GIS) provide the spatial framework necessary for combining diverse environmental datasets into cohesive risk assessments. By layering multiple types of terrain and environmental data, GIS enables analysts to identify areas with varying levels of landslide susceptibility.",
          "GIS technology allows researchers to visualize spatial relationships between landslide occurrences and environmental factors, making it possible to identify patterns that would be difficult to detect through ground observation alone."
        ]
      },
      {
        heading: "Combining Spatial Layers",
        content: [
          "A landslide risk map is typically constructed by combining several spatial data layers, each representing a different environmental factor. Elevation data provides information about terrain height, while slope and aspect layers describe the steepness and orientation of the landscape.",
          "Land use and soil characteristic layers add information about surface conditions, while vegetation indices such as NDVI indicate the health and density of plant cover. Rainfall distribution layers add meteorological context, and historical landslide location data provides empirical evidence of past slope failures."
        ]
      },
      {
        heading: "From Layers to Risk Maps",
        content: [
          "By assigning weights to different environmental factors based on their observed relationship with historical landslide occurrences, GIS analysts can produce composite risk maps that highlight areas with elevated susceptibility. These maps serve as practical tools for land-use planning, emergency preparedness, and monitoring resource allocation.",
          "Our interactive GIS risk map applies this layered approach to the Northeast India region, combining real-time environmental data with terrain characteristics to provide district-level risk visualizations."
        ]
      },
      {
        heading: "Limitations and Considerations",
        content: [
          "GIS-based risk maps represent a model of reality and are subject to data quality, resolution, and methodological assumptions. They provide useful guidance for identifying areas of potential risk but should be interpreted as part of a broader disaster-management framework that includes ground verification and continuous monitoring."
        ]
      }
    ]
  },
  {
    id: "3",
    slug: "machine-learning-landslide-risk",
    category: "ARTIFICIAL INTELLIGENCE",
    title: "How Machine Learning Can Predict Landslide Risk",
    excerpt: "Machine learning algorithms analyze historical landslide data and environmental features to estimate risk probability and classify susceptibility levels.",
    readTime: "8 min read",
    featured: true,
    publishedAt: "2026-08-25",
    author: "LRM Research Team",
    content: [
      {
        heading: "Machine Learning in Landslide Risk Assessment",
        content: [
          "Machine learning provides a data-driven approach to landslide risk assessment by learning patterns from historical landslide data and associated environmental conditions. Rather than relying on manually defined rules, these algorithms identify statistical relationships between environmental features and landslide occurrence.",
          "This approach is particularly valuable in regions like Northeast India, where complex terrain and diverse environmental conditions create challenges for traditional assessment methods."
        ]
      },
      {
        heading: "Features Used in Prediction",
        content: [
          "Effective machine learning models for landslide risk assessment typically incorporate a range of environmental features. Rainfall accumulation and intensity provide meteorological context, while soil moisture indicators reflect subsurface conditions that affect slope stability.",
          "Topographic features such as elevation, slope angle, and terrain curvature describe the physical landscape. Vegetation indices like NDVI capture the state of plant cover, and temperature data adds seasonal context. Soil type classification provides information about the geological substrate.",
          "Feature engineering — the process of transforming raw environmental data into meaningful model inputs — is a critical step. For example, computing the difference between surface and deep soil moisture, or calculating cumulative rainfall over multiple days, can reveal patterns that raw measurements alone might not capture."
        ]
      },
      {
        heading: "The Prediction Workflow",
        content: [
          "The conceptual workflow for machine learning-based landslide risk assessment follows a structured pipeline: Environmental Data → Feature Engineering → Model Training → Risk Probability → Risk Classification.",
          "Environmental data is collected from sensors, satellites, and historical records. This data is then transformed through feature engineering to create meaningful inputs. The machine learning model learns from historical examples where landslide outcomes are known, and then applies these learned patterns to new environmental conditions to estimate risk probability.",
          "The probability output can be classified into risk levels — such as low, moderate, high, or critical — to support decision-making and alert generation."
        ]
      },
      {
        heading: "Our Three-Layer Pipeline",
        content: [
          "Our platform implements a three-layer machine learning pipeline for landslide risk prediction. The first layer uses XGBoost classification to estimate risk probability based on engineered environmental features. The second layer applies Agglomerative Hierarchical Clustering to group locations by soil type, terrain, and moisture characteristics. The third layer combines these outputs through a spatial decision model to produce a final risk classification.",
          "This layered approach leverages the strengths of different algorithms — the predictive accuracy of gradient boosting, the pattern recognition of clustering, and the integration capability of a meta-learner — to produce more robust risk estimates. However, like all model-based approaches, the outputs represent probability estimates and should be used as one component of a comprehensive risk management strategy."
        ]
      }
    ]
  },
  {
    id: "4",
    slug: "rainfall-soil-moisture-landslide-risk",
    category: "ENVIRONMENTAL MONITORING",
    title: "Why Rainfall and Soil Moisture Matter for Landslide Risk",
    excerpt: "Rainfall accumulation and soil saturation are key environmental indicators, but understanding their combined effect requires monitoring multiple variables.",
    readTime: "6 min read",
    featured: false,
    publishedAt: "2026-09-01",
    author: "LRM Research Team",
    content: [
      {
        heading: "Rainfall as a Landslide Trigger",
        content: [
          "Rainfall is widely recognized as one of the primary triggers of landslides, particularly in regions with steep terrain and vulnerable soil conditions. The relationship between rainfall and landslide occurrence, however, is not straightforward — it depends on rainfall intensity, duration, accumulation, and the antecedent moisture conditions of the soil.",
          "Intense short-duration rainfall can cause rapid increases in pore-water pressure, leading to shallow landslides and debris flows. Longer periods of moderate rainfall can gradually saturate deeper soil layers, potentially triggering deeper-seated slope failures."
        ]
      },
      {
        heading: "Soil Moisture and Slope Stability",
        content: [
          "Soil moisture is a direct indicator of the water content within the ground, and it plays a critical role in determining slope stability. As soil moisture increases, pore-water pressure rises, reducing the effective stress that holds soil particles together. This reduction in soil strength can eventually lead to slope failure.",
          "Monitoring soil moisture at different depths provides valuable information about subsurface conditions. Surface moisture may respond quickly to rainfall, while deeper moisture levels change more slowly and reflect longer-term saturation trends. The difference between surface and deep moisture can indicate how water is moving through the soil profile."
        ]
      },
      {
        heading: "Why Multiple Indicators Matter",
        content: [
          "While rainfall data alone can provide useful information, it may not be sufficient for accurate risk assessment. Two locations experiencing the same rainfall can respond very differently depending on their soil type, slope angle, vegetation cover, and drainage characteristics.",
          "By combining rainfall monitoring with soil moisture measurements, terrain analysis, and vegetation indices, it becomes possible to develop a more complete picture of slope conditions. Our real-time environmental monitoring system tracks multiple variables simultaneously, providing a more comprehensive basis for risk assessment than any single indicator alone."
        ]
      },
      {
        heading: "Connecting to Our Monitoring System",
        content: [
          "Our platform continuously monitors rainfall and soil moisture conditions across Northeast India, integrating these measurements with terrain data and vegetation indices. This multi-variable approach supports more informed risk assessments and helps identify areas where environmental conditions may be approaching thresholds associated with increased landslide susceptibility."
        ]
      }
    ]
  },
  {
    id: "5",
    slug: "satellite-landslide-monitoring",
    category: "SATELLITE MONITORING",
    title: "Watching the Landscape from Space: Satellites and Landslide Monitoring",
    excerpt: "Satellite imagery and remote sensing provide scalable observations of terrain change, vegetation health, and environmental conditions across large areas.",
    readTime: "7 min read",
    featured: false,
    publishedAt: "2026-09-03",
    author: "LRM Research Team",
    content: [
      {
        heading: "Remote Sensing for Landslide Assessment",
        content: [
          "Remote sensing technologies, particularly satellite-based observation systems, provide a scalable approach to monitoring environmental conditions across large and often inaccessible terrain. By capturing multispectral imagery at regular intervals, satellites enable the tracking of changes in land cover, vegetation health, and surface characteristics over time.",
          "This capability is especially valuable in mountainous regions like Northeast India, where ground-based monitoring networks may have limited spatial coverage due to terrain constraints."
        ]
      },
      {
        heading: "Satellite-Derived Information Layers",
        content: [
          "Satellite imagery provides several types of information relevant to landslide risk assessment. Multispectral data can be used to compute vegetation indices such as NDVI, which indicates the health and density of plant cover. Changes in NDVI over time can signal vegetation stress or land-use changes that may affect slope stability.",
          "Digital elevation models derived from satellite or airborne sensors provide terrain information including slope, aspect, and elevation. Synthetic Aperture Radar (SAR) data can be used to monitor ground surface deformation, potentially identifying slow-moving slopes before they fail catastrophically.",
          "Change detection techniques applied to multi-temporal satellite imagery can reveal landscape modifications such as deforestation, new construction, or natural erosion that may alter landslide susceptibility."
        ]
      },
      {
        heading: "Complementing Ground Observations",
        content: [
          "Satellite-derived information is most effective when combined with ground-based observations and historical landslide inventories. While satellites provide broad spatial coverage, ground measurements offer higher temporal resolution and direct observations of subsurface conditions that satellites cannot detect.",
          "Our platform integrates satellite-derived terrain and vegetation data with ground-based environmental monitoring to provide a more comprehensive view of landslide risk conditions across the region."
        ]
      },
      {
        heading: "Limitations of Satellite Monitoring",
        content: [
          "Satellite imagery is subject to limitations including cloud cover (which is frequent in Northeast India during monsoon seasons), spatial resolution constraints, and revisit intervals. Additionally, satellite data provides information about surface conditions but cannot directly measure subsurface soil moisture or pore-water pressure.",
          "For these reasons, satellite monitoring should be considered as one component of a multi-source approach to landslide risk assessment, rather than a standalone prediction tool."
        ]
      }
    ]
  },
  {
    id: "6",
    slug: "risk-maps-to-early-warning",
    category: "EARLY WARNING",
    title: "From Risk Maps to Early Warning: What Happens After Prediction?",
    excerpt: "Risk maps identify areas of potential concern, but effective early warning systems require continuous monitoring, threshold management, and timely communication.",
    readTime: "7 min read",
    featured: false,
    publishedAt: "2026-09-05",
    author: "LRM Research Team",
    content: [
      {
        heading: "Understanding the Terminology",
        content: [
          "Landslide risk management involves several related but distinct concepts that are often confused. Susceptibility refers to the inherent tendency of an area to experience landslides based on terrain, geology, and environmental conditions. Hazard assessment evaluates the probability of landslide occurrence in a given area over a specific time period.",
          "Risk assessment goes further by considering the potential consequences of landslide events, including impacts on infrastructure, population, and economic activity. Monitoring involves the continuous or periodic observation of environmental conditions in areas identified as potentially at risk.",
          "Prediction refers to the estimation of when and where a landslide might occur, which remains an extremely challenging scientific problem. Early warning is the process of communicating potential risk to affected populations and authorities in time for protective action to be taken."
        ]
      },
      {
        heading: "From Assessment to Action",
        content: [
          "Risk maps — whether based on historical data, environmental indicators, or machine learning outputs — provide a spatial representation of where landslide risk may be elevated. These maps are valuable planning tools, but they represent a snapshot of potential risk rather than a real-time prediction of imminent events.",
          "To move from risk assessment to early warning, continuous monitoring of environmental conditions is necessary. When monitoring data indicates that conditions in a high-risk area are approaching or exceeding historically observed thresholds associated with landslide activity, this information can trigger alerts and inform decision-making."
        ]
      },
      {
        heading: "Our Integrated Approach",
        content: [
          "Our platform connects several components of the landslide risk management chain. The risk map provides spatial context for identifying areas of concern. Environmental monitoring tracks conditions in real time. Machine learning models estimate risk probability based on current conditions. The alert system communicates potential risk to stakeholders.",
          "This integrated approach — combining risk mapping, monitoring, prediction, and alerts — represents one component of a broader disaster-management workflow that also includes land-use planning, infrastructure resilience, community preparedness, and emergency response."
        ]
      },
      {
        heading: "Prediction as Part of the Solution",
        content: [
          "It is important to recognize that prediction is one element within a comprehensive disaster-risk reduction framework. No prediction system can guarantee the exact time and location of every landslide event. The value of prediction lies in its ability to support proactive monitoring and preparedness, reducing the window of uncertainty between observation and action.",
          "By continuously refining models with new data and integrating multiple information sources, prediction accuracy can improve over time — but effective early warning systems always incorporate multiple lines of evidence and human judgment alongside algorithmic outputs."
        ]
      }
    ]
  }
];

export const CATEGORIES = [
  "ALL",
  "LANDSLIDE SCIENCE",
  "GIS & REMOTE SENSING",
  "ARTIFICIAL INTELLIGENCE",
  "ENVIRONMENTAL MONITORING",
  "SATELLITE MONITORING",
  "EARLY WARNING"
];

export function getFeaturedArticles(): Article[] {
  return ARTICLES.filter((a) => a.featured);
}

export function getArticleBySlug(slug: string): Article | undefined {
  return ARTICLES.find((a) => a.slug === slug);
}

export function getRelatedArticles(article: Article, limit = 3): Article[] {
  return ARTICLES.filter((a) => a.id !== article.id && a.category === article.category).slice(0, limit);
}

export function searchArticles(query: string): Article[] {
  const q = query.toLowerCase();
  return ARTICLES.filter(
    (a) =>
      a.title.toLowerCase().includes(q) ||
      a.category.toLowerCase().includes(q) ||
      a.excerpt.toLowerCase().includes(q)
  );
}

export function filterByCategory(category: string): Article[] {
  if (category === "ALL") return ARTICLES;
  return ARTICLES.filter((a) => a.category === category);
}
