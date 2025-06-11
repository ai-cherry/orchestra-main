import type { Metadata } from "next"
import { Inter } from 'next/font/google'
import "./globals.css"
import { PersonaProvider } from "@/contexts/PersonaContext"

const inter = Inter({ subsets: ["latin"] })

export const metadata: Metadata = {
  title: "Cherry AI Orchestrator",
  description: "Advanced AI admin interface with sophisticated agent swarm management",
}

export default function tLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.className} bg-black text-white antialiased`}>
        <PersonaProvider>
          {children}
        </PersonaProvider>
      </body>
    </html>
  )
} 