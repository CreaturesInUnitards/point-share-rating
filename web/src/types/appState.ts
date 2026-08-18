import type { osydComponent, StoreActions } from 'osyd'

import type { PsrState } from '../state/psrState'

export type AppState = PsrState
export type Actions = StoreActions<AppState>

export type OC<Props = object, Dom extends Element = Element> = osydComponent<
  Props,
  AppState,
  Actions,
  Dom
>
