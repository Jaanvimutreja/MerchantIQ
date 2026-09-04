import "./globals.css";

export const metadata = {
  title: "BargainAI — Merchant Bargaining Operations",
  description: "AI-powered merchant bargaining and dynamic pricing platform",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-gray-50 text-gray-900 antialiased font-sans">
        {/* Top navigation */}
        <header className="bg-white border-b border-gray-200 sticky top-0 z-30 shadow-xs">
          <div className="max-w-7xl xl:max-w-[1360px] mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <a href="/" className="flex items-center gap-2.5 group">
                <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center text-white font-bold text-sm shadow-xs group-hover:bg-blue-700 transition-colors">
                  B
                </div>
                <div className="flex items-baseline gap-1.5">
                  <span className="text-lg font-bold text-gray-900 tracking-tight">
                    Bargain<span className="text-blue-600">AI</span>
                  </span>
                </div>
              </a>
              <span className="hidden sm:inline-flex items-center px-2 py-0.5 text-xs font-medium text-blue-700 bg-blue-50 border border-blue-200 rounded-md">
                Merchant Operations
              </span>
            </div>

            <nav className="flex items-center gap-3 sm:gap-4">
              <a
                href="/"
                className="text-xs sm:text-sm font-semibold text-gray-700 hover:text-blue-600 transition-colors"
              >
                Dashboard
              </a>
              <a
                href="/create"
                className="inline-flex items-center gap-1.5 px-3.5 py-1.5 bg-blue-600 text-white text-xs font-semibold rounded-lg hover:bg-blue-700 transition-colors shadow-xs"
              >
                <span className="text-sm leading-none">+</span> New Bargain
              </a>
            </nav>
          </div>
        </header>

        <main className="max-w-7xl xl:max-w-[1360px] mx-auto px-4 sm:px-6 lg:px-8 pt-8 pb-16">{children}</main>
      </body>
    </html>
  );
}

