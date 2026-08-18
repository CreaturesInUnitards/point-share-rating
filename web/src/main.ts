import './style.css'

import o from 'osyd'

import { GamesPage } from './pages/games'
import { MethodsPage } from './pages/methods'
import { RatingsPage } from './pages/ratings'
import { fetchPsrData } from './services/psrData'
import { psrDefaultState } from './state/psrState'
import type { AppState } from './types/appState'

o.route.prefix = '#!'

const store = o.createState<AppState>({ defaultState: psrDefaultState })

o.route(
  document.body,
  '/',
  {
    '/': RatingsPage,
    '/games': GamesPage,
    '/methods': MethodsPage,
  },
  { state: store },
)

fetchPsrData()
  .then(data => {
    store.setPsr(data)
    store.setPsrStatus('ready')
  })
  .catch(() => store.setPsrStatus('error'))
