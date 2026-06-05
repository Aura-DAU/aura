import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "Dhirubhai Ambani University Portal",
    short_name: "DAU Portal",
    description: "Progressive Web App for Dhirubhai Ambani University, enriched with AI.",
    start_url: "/student/academics",
    display: "standalone",
    background_color: "#0A1628",
    theme_color: "#E8400C",
    icons: [
      {
        src: "/icons/icon-192x192.png",
        sizes: "192x192",
        type: "image/png",
        purpose: "any",
      },
      {
        src: "/icons/icon-512x512.png",
        sizes: "512x512",
        type: "image/png",
        purpose: "any",
      },
      {
        src: "/icons/icon-512x512-maskable.png",
        sizes: "512x512",
        type: "image/png",
        purpose: "maskable",
      },
    ],
    shortcuts: [
      {
        name: "Academics",
        url: "/student/academics",
        description: "View courses, timetables, and academic calendar",
      },
      {
        name: "Placements",
        url: "/student/placements",
        description: "View preparation resources, placement drives, and statistics",
      },
    ],
  };
}
