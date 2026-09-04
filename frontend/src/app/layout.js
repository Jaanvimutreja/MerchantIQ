import "./globals.css";

export const metadata = {
  title: "BargainAI",
  description: "AI-powered merchant bargaining system",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-gray-50">
        {/* Top navigation */}
        <header className="bg-white border-b border-gray-200">
          <div className="max-w-6xl mx-auto px-6 h-14 flex items-center justify-between">
            <a href="/" className="text-lg font-semibold text-gray-900 tracking-tight">
              BargainAI
            </a>
            <span className="text-xs text-gray-400 font-medium">Merchant Console</span>
          </div>
        </header>

        <main className="max-w-6xl mx-auto px-6 py-8">{children}</main>
      </body>
    </html>
  );
}
