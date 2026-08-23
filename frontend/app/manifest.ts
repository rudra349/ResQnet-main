import { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "ResQNet — Disaster Response Intelligence",
    short_name: "ResQNet",
    description: "Persistent-memory AI disaster response coordination PWA",
    start_url: "/",
    display: "standalone",
    background_color: "#0A0E14",
    theme_color: "#FF6B35",
    icons: [
      {
        src: "/icon-192.png",
        sizes: "192x192",
        type: "image/png",
      },
      {
        src: "/icon-512.png",
        sizes: "512x512",
        type: "image/png",
      },
    ],
  };
}
