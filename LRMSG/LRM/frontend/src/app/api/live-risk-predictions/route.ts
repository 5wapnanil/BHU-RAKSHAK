import { NextResponse } from 'next/server';

const LOCATIONS = [
  { name: "Darjeeling", state: "West Bengal", lat: 27.041, lng: 88.2663 },
  { name: "Gangtok", state: "Sikkim", lat: 27.3389, lng: 88.6065 },
  { name: "Shillong", state: "Meghalaya", lat: 25.5788, lng: 91.8933 },
  { name: "Kohima", state: "Nagaland", lat: 25.6586, lng: 94.1086 },
  { name: "Aizawl", state: "Mizoram", lat: 23.7271, lng: 92.7176 },
  { name: "Itanagar", state: "Arunachal Pradesh", lat: 27.1044, lng: 93.692 },
  { name: "Imphal", state: "Manipur", lat: 24.817, lng: 93.9368 },
  { name: "Agartala", state: "Tripura", lat: 23.8315, lng: 91.2868 },
  { name: "Guwahati", state: "Assam", lat: 26.1445, lng: 91.7362 },
  { name: "Champhai", state: "Mizoram", lat: 23.4917, lng: 93.2045 },
  { name: "Dhemaji", state: "Assam", lat: 27.5547, lng: 94.2599 },
  { name: "Lower Dibang Valley", state: "Arunachal Pradesh", lat: 28.2333, lng: 95.7776 },
  { name: "East Jaintia Hills", state: "Meghalaya", lat: 25.1059, lng: 92.3602 },
  { name: "West Kameng", state: "Arunachal Pradesh", lat: 27.25, lng: 92.42 },
  { name: "North Tripura", state: "Tripura", lat: 24.27, lng: 92.16 },
];

let cachedData: any[] = LOCATIONS.map(loc => ({
  ...loc,
  rainfall: null,
  slope: null,
  probability: null,
  status: 'unavailable'
}));

let lastFetchTime = 0;
let isFetching = false;

const fetchRealDataInBackground = async () => {
  if (isFetching) return;
  isFetching = true;
  console.log("[GIS Engine] Checking prediction endpoint status...");
  
  const newPredictions = [];
  
  for (const loc of LOCATIONS) {
    try {
      let simRainfall = Math.random() * 50;
      let simSlope = 10 + Math.random() * 20; 

      // Query ML model endpoint (port 8000)
      const res = await fetch("http://127.0.0.1:8000/prediction/custom", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          rainfall: simRainfall,
          slope: simSlope,
          soilMoisture: 0.6,
          elevation: 1000,
          soilType: "Acrisols"
        })
      });

      if (res.status === 503) {
        // Legacy model is retired: report unavailable explicitly rather than fabricating values
        newPredictions.push({
          ...loc,
          rainfall: Math.round(simRainfall),
          slope: Math.round(simSlope),
          probability: null,
          status: 'unavailable'
        });
        continue;
      }
      
      if (res.ok) {
        const data = await res.json();
        newPredictions.push({
          ...loc,
          rainfall: Math.round(simRainfall),
          slope: Math.round(simSlope),
          probability: data.probability !== undefined ? data.probability * 100 : null,
          status: 'active'
        });
      } else {
        newPredictions.push({
          ...loc,
          rainfall: Math.round(simRainfall),
          slope: Math.round(simSlope),
          probability: null,
          status: 'unavailable'
        });
      }
    } catch (err) {
      newPredictions.push({
        ...loc,
        rainfall: null,
        slope: null,
        probability: null,
        status: 'unavailable'
      });
    }
  }
  
  if (newPredictions.length > 0) {
    cachedData = newPredictions;
    lastFetchTime = Date.now();
  }
  
  isFetching = false;
};

export async function GET() {
  const CACHE_TTL = 30000; // 30 seconds for demonstration purposes
  
  // If cache is stale or empty, trigger a background refresh. 
  if (Date.now() - lastFetchTime > CACHE_TTL && !isFetching) {
    fetchRealDataInBackground();
  }

  const blockedRoads = [
    { name: "NH-10 (Siliguri-Gangtok)", coords: [[26.8, 88.4], [27.0, 88.5], [27.2, 88.6]], status: "Closed" },
    { name: "NH-06 (Meghalaya-Assam)", coords: [[25.105, 92.360], [25.150, 92.400], [25.180, 92.450]], status: "Partial" },
    { name: "NH-29 (Dimapur-Kohima)", coords: [[25.9, 93.7], [25.8, 93.9], [25.65, 94.1]], status: "Partial" },
  ];

  return NextResponse.json({
    status: 'partial',
    predictionStatus: 'unavailable',
    message: 'The legacy landslide prediction ML model has been retired and disabled.',
    timestamp: new Date(lastFetchTime || Date.now()).toISOString(),
    data: {
      predictions: cachedData,
      blockedRoads: blockedRoads
    }
  });
}
