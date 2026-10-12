import { useEffect, useRef, useState } from 'react'

const API_GOC = 'http://127.0.0.1:8000'

// Làn UI độc lập làn nội dung: chọn ngôn ngữ lạ thì tạm tiếng Anh + pending,
// dịch nền xong thì tự chuyển khi ready.
export function useUiBundle(locale: string): { t: (khoa: string) => string; sanSang: boolean } {
  const [bundle, setBundle] = useState<Record<string, string>>({})
  const [sanSang, setSanSang] = useState(false)
  const [localeDaTai, setLocaleDaTai] = useState(locale)
  const huyRef = useRef(false)

  // Đổi locale thì reset readiness ngay khi render, không chờ effect.
  if (locale !== localeDaTai) {
    setLocaleDaTai(locale)
    setSanSang(false)
  }

  useEffect(() => {
    huyRef.current = false
    let dem = 0
    const tai = async () => {
      try {
        const res = await fetch(`${API_GOC}/ui-bundles/${locale}`)
        const goi = (await res.json()) as { status: string; bundle: Record<string, string> }
        if (huyRef.current) return
        setBundle(goi.bundle)
        if (goi.status === 'ready' || dem >= 10) {
          setSanSang(goi.status === 'ready')
          return
        }
        dem += 1
        window.setTimeout(() => void tai(), 3000)
      } catch {
        if (!huyRef.current) setSanSang(false)
      }
    }
    void tai()
    return () => {
      huyRef.current = true
    }
  }, [locale])

  return { t: (khoa: string) => bundle[khoa] ?? khoa, sanSang }
}
