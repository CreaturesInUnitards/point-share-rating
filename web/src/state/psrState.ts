export interface PsrTeam {
  team: string
  name: string
  rating: number
  delta: number
  raw: number
  recency: number
  recencyNote: string
  schedule: number
  scheduleNote: string
  prior: number
  priorNote: string
  games: number
  qb: string
  qbPts: number
  traj: number[]
}

export interface PsrGame {
  away: string
  home: string
  pred: number
  as?: number
  hs?: number
  vegas?: number | null
}

export interface PsrGamesBlock {
  resSeason?: number
  resWeek?: number
  results?: PsrGame[]
  upSeason?: number | null
  upWeek?: number | null
  upcoming?: PsrGame[]
}

export interface PsrData {
  season: number
  week: number
  built: string
  teams: PsrTeam[]
  games?: PsrGamesBlock
}

export type PsrStatus = 'loading' | 'ready' | 'error'

export type PsrState = {
  $psr: PsrData | null
  $psrStatus: PsrStatus
}

export const psrDefaultState: PsrState = {
  $psr: null,
  $psrStatus: 'loading',
}
