import type { PsrData } from '../state/psrState'

export const fetchPsrData = async (): Promise<PsrData> => {
  const res = await fetch(`${import.meta.env.BASE_URL}ratings.json`)
  if (!res.ok) throw new Error(`ratings.json: HTTP ${res.status}`)
  return (await res.json()) as PsrData
}
