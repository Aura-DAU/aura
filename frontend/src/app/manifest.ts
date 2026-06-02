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
        src: "/dau_logo.png",
        sizes: "1920x912",
        type: "image/png",
        purpose: "any",
      },
      {
        src: "/dau_logo.jpg",
        sizes: "1920x912",
        type: "image/jpeg",
        purpose: "any",
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
