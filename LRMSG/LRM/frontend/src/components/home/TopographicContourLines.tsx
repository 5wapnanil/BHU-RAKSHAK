export default function TopographicContourLines() {
  return (
    <div
      aria-hidden="true"
      style={{
        position: "absolute",
        top: 0,
        right: 0,
        width: "100%",
        maxWidth: "1440px",
        height: "720px",
        overflow: "hidden",
        pointerEvents: "none",
        zIndex: 0,
        opacity: 0.85,
      }}
    >
      <svg
        viewBox="0 0 1200 650"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        style={{
          width: "100%",
          height: "100%",
          display: "block",
        }}
      >
        <g stroke="rgba(170, 132, 102, 0.18)" strokeWidth="1.2">
          {/* Topographic Elevation Curves */}
          <path d="M450,-50 C650,80 820,60 1000,-20 C1100,-60 1220,-10 1300,50" />
          <path d="M480,20 C680,140 850,110 1040,40 C1130,5 1200,60 1280,110" />
          <path d="M520,90 C710,200 890,170 1070,100 C1160,65 1210,130 1300,180" />
          <path d="M570,160 C750,260 920,230 1100,160 C1190,125 1230,200 1320,240" />
          <path d="M620,230 C790,320 950,290 1130,220 C1220,185 1260,260 1350,300" />
          <path d="M680,300 C830,380 990,350 1160,280 C1250,245 1280,320 1380,360" />
          <path d="M740,370 C880,440 1030,410 1200,340 C1280,305 1310,380 1400,420" />
          <path d="M800,440 C930,500 1080,470 1240,400 C1310,365 1340,430 1420,480" />
          
          {/* Valley & Slope Contour Folds */}
          <path d="M720,-40 C850,150 780,290 940,420 C1040,500 1180,480 1280,560" strokeDasharray="3 4" strokeOpacity="0.6" />
          <path d="M820,-30 C940,140 890,270 1020,380 C1110,460 1220,450 1320,520" />
          <path d="M920,-20 C1020,130 980,250 1100,340 C1180,410 1280,420 1360,480" />
          <path d="M1020,-10 C1100,120 1070,220 1180,300 C1250,360 1320,380 1400,430" />
        </g>
      </svg>
    </div>
  );
}
