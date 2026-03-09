export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24 bg-gradient-to-br from-gray-900 to-gray-800">
      <div className="text-center">
        <h1 className="text-5xl font-bold text-white mb-4">
          {{PROJE_AD}}
        </h1>
        <p className="text-xl text-gray-400 mb-8">
          {{PROJE_ACIKLAMA}}
        </p>
        <div className="flex gap-4 justify-center">
          <a href="/docs" className="px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition">
            Dokümantasyon
          </a>
          <a href="/api" className="px-6 py-3 border border-gray-600 text-gray-300 rounded-lg hover:bg-gray-700 transition">
            API
          </a>
        </div>
      </div>
    </main>
  )
}
