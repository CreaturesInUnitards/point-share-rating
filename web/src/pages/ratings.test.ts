import { vfSpark } from './ratings'

interface SparkVnode {
  props: { points?: string }
  children?: SparkVnode[]
}

test('vfSpark scales the trajectory across the full width', () => {
  const svg = vfSpark([48, 50, 52]) as unknown as SparkVnode
  const polyline = (svg.children ?? []).find(c => c?.props?.points)
  expect(polyline).toBeDefined()
  const xs = polyline!.props
    .points!.split(' ')
    .map(p => Number(p.split(',')[0]))
  expect(xs[0]).toBe(0)
  expect(xs[xs.length - 1]).toBe(72)
})

test('vfSpark tolerates a single-week trajectory', () => {
  const svg = vfSpark([50]) as unknown as SparkVnode
  const polyline = (svg.children ?? []).find(c => c?.props?.points)
  expect(polyline!.props.points).not.toContain('NaN')
})
