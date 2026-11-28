export type ExerciseKind = 'Push-up' | 'Squat' | 'Sit-up'
export type DifficultyLevel = 'Beginner' | 'Intermediate' | 'Advanced'
export type TargetStatus = 'far' | 'near' | 'reached' | 'exceeded'

export interface TrainingSet {
  id: string
  reps: number
  restSeconds: number
}

export interface TrainingPlan {
  id: string
  name: string
  description: string
  exercise: ExerciseKind
  difficulty: DifficultyLevel
  targetMinutes: number
  customTotalReps?: number
  sets: TrainingSet[]
}

export interface TargetEvaluation {
  status: TargetStatus
  percentage: number
  targetReps: number
  targetMinutes: number
  actualReps: number
  actualDurationSec: number
  completedSets: number
  totalSets: number
  diffReps: number
  badge: string
  headline: string
  summary: string
  timeNote: string
}

export const DEFAULT_TRAINING_PLANS: TrainingPlan[] = [
  {
    id: 'plan-pushup-50',
    name: 'Ultimate',
    description: 'Intense Push Up Challenge',
    exercise: 'Push-up',
    difficulty: 'Advanced',
    targetMinutes: 1.5,
    sets: [
      { id: 's1', reps: 20, restSeconds: 30 },
      { id: 's2', reps: 15, restSeconds: 30 },
      { id: 's3', reps: 15, restSeconds: 30 },
    ],
  },
  {
    id: 'plan-squat-40',
    name: 'Squat Stamina',
    description: 'Latihan kekuatan kaki & kedalaman squat konsisten',
    exercise: 'Squat',
    difficulty: 'Intermediate',
    targetMinutes: 2.5,
    sets: [
      { id: 's1', reps: 15, restSeconds: 30 },
      { id: 's2', reps: 15, restSeconds: 30 },
      { id: 's3', reps: 10, restSeconds: 20 },
    ],
  },
  {
    id: 'plan-situp-30',
    name: 'Core Sit-up',
    description: 'Penguatan otot inti dengan tempo stabil',
    exercise: 'Sit-up',
    difficulty: 'Beginner',
    targetMinutes: 2,
    sets: [
      { id: 's1', reps: 10, restSeconds: 25 },
      { id: 's2', reps: 10, restSeconds: 25 },
      { id: 's3', reps: 10, restSeconds: 25 },
    ],
  },
]

export interface ExerciseRecommendation {
  id: string
  label: string
  exercise: ExerciseKind
  difficulty: DifficultyLevel
  targetMinutes: number
  description: string
  sets: { reps: number; restSeconds: number }[]
}

export const EXERCISE_RECOMMENDATIONS: Record<ExerciseKind, ExerciseRecommendation[]> = {
  'Push-up': [
    {
      id: 'rec-pushup-beg',
      label: 'Pemula · 30 reps',
      exercise: 'Push-up',
      difficulty: 'Beginner',
      targetMinutes: 2,
      description: '3 set x 10 reps untuk membangun form push-up bersih',
      sets: [
        { reps: 10, restSeconds: 30 },
        { reps: 10, restSeconds: 30 },
        { reps: 10, restSeconds: 30 },
      ],
    },
    {
      id: 'rec-pushup-int',
      label: 'Standar · 50 reps',
      exercise: 'Push-up',
      difficulty: 'Intermediate',
      targetMinutes: 2,
      description: '20 + 15 + 15 push-up dengan istirahat 30 detik',
      sets: [
        { reps: 20, restSeconds: 30 },
        { reps: 15, restSeconds: 30 },
        { reps: 15, restSeconds: 30 },
      ],
    },
    {
      id: 'rec-pushup-adv',
      label: 'Ekstra · 75 reps',
      exercise: 'Push-up',
      difficulty: 'Advanced',
      targetMinutes: 3,
      description: 'Tantangan daya tahan upper body 3 x 25 reps',
      sets: [
        { reps: 25, restSeconds: 35 },
        { reps: 25, restSeconds: 35 },
        { reps: 25, restSeconds: 30 },
      ],
    },
  ],
  'Sit-up': [
    {
      id: 'rec-situp-beg',
      label: 'Pemula · 30 reps',
      exercise: 'Sit-up',
      difficulty: 'Beginner',
      targetMinutes: 2,
      description: '3 set x 10 reps untuk aktivasi otot inti stabil',
      sets: [
        { reps: 10, restSeconds: 25 },
        { reps: 10, restSeconds: 25 },
        { reps: 10, restSeconds: 25 },
      ],
    },
    {
      id: 'rec-situp-int',
      label: 'Standar · 45 reps',
      exercise: 'Sit-up',
      difficulty: 'Intermediate',
      targetMinutes: 2.5,
      description: '3 set x 15 reps dengan ritme terkontrol',
      sets: [
        { reps: 15, restSeconds: 30 },
        { reps: 15, restSeconds: 30 },
        { reps: 15, restSeconds: 30 },
      ],
    },
    {
      id: 'rec-situp-adv',
      label: 'Ekstra · 60 reps',
      exercise: 'Sit-up',
      difficulty: 'Advanced',
      targetMinutes: 3,
      description: '3 set x 20 reps untuk ketahanan core maksimal',
      sets: [
        { reps: 20, restSeconds: 30 },
        { reps: 20, restSeconds: 30 },
        { reps: 20, restSeconds: 30 },
      ],
    },
  ],
  Squat: [
    {
      id: 'rec-squat-beg',
      label: 'Pemula · 30 reps',
      exercise: 'Squat',
      difficulty: 'Beginner',
      targetMinutes: 2,
      description: '3 set x 10 reps fokus kedalaman squat > 70%',
      sets: [
        { reps: 10, restSeconds: 30 },
        { reps: 10, restSeconds: 30 },
        { reps: 10, restSeconds: 30 },
      ],
    },
    {
      id: 'rec-squat-int',
      label: 'Standar · 45 reps',
      exercise: 'Squat',
      difficulty: 'Intermediate',
      targetMinutes: 2.5,
      description: '3 set x 15 reps untuk kekuatan kaki & pinggul',
      sets: [
        { reps: 15, restSeconds: 30 },
        { reps: 15, restSeconds: 30 },
        { reps: 15, restSeconds: 30 },
      ],
    },
    {
      id: 'rec-squat-adv',
      label: 'Ekstra · 60 reps',
      exercise: 'Squat',
      difficulty: 'Advanced',
      targetMinutes: 3,
      description: '3 set x 20 reps latihan intensitas tinggi lower body',
      sets: [
        { reps: 20, restSeconds: 35 },
        { reps: 20, restSeconds: 35 },
        { reps: 20, restSeconds: 30 },
      ],
    },
  ],
}

export function getPlanTotalReps(plan: TrainingPlan): number {
  if (typeof plan.customTotalReps === 'number' && plan.customTotalReps > 0) {
    return Math.round(plan.customTotalReps)
  }
  return plan.sets.reduce((sum, s) => sum + Math.max(0, s.reps), 0)
}

export function distributeRepsAcrossSets(totalReps: number, sets: TrainingSet[]): TrainingSet[] {
  const count = Math.max(1, sets.length)
  const safeTotal = Math.max(count, Math.round(totalReps))
  const base = Math.floor(safeTotal / count)
  const remainder = safeTotal % count
  return sets.map((s, idx) => ({
    ...s,
    reps: base + (idx < remainder ? 1 : 0),
  }))
}

export function estimatePlanMinutes(sets: TrainingSet[], totalOverride?: number): number {
  const sumReps = sets.reduce((sum, s) => sum + Math.max(0, s.reps), 0)
  const totalReps = typeof totalOverride === 'number' && totalOverride > 0 ? totalOverride : sumReps
  const restBetweenSets = sets
    .slice(0, Math.max(0, sets.length - 1))
    .reduce((sum, s) => sum + Math.max(0, s.restSeconds), 0)
  const totalSeconds = totalReps * 1.5 + restBetweenSets
  return Math.max(0.5, Math.round((totalSeconds / 60) * 2) / 2)
}

export function getCompletedSetsCount(actualReps: number, sets: TrainingSet[]): number {
  let cumulative = 0
  let completed = 0
  for (const s of sets) {
    cumulative += Math.max(1, s.reps)
    if (actualReps >= cumulative) {
      completed += 1
    } else {
      break
    }
  }
  return completed
}

export function formatSecondsClock(totalSeconds: number): string {
  const safe = Math.max(0, Math.round(totalSeconds))
  const mm = Math.floor(safe / 60)
    .toString()
    .padStart(2, '0')
  const ss = (safe % 60).toString().padStart(2, '0')
  return `${mm}:${ss}`
}

export function formatMinutesClock(minutes: number): string {
  return formatSecondsClock(Math.round(Math.max(0.5, minutes) * 60))
}

export function evaluateWorkoutTarget(
  actualReps: number,
  actualDurationSec: number,
  targetReps: number,
  targetMinutes: number,
  lang: 'id' | 'en' = 'id',
  completedSets = 0,
  totalSets = 1,
): TargetEvaluation {
  const safeTargetReps = Math.max(1, targetReps)
  const safeActualReps = Math.max(0, actualReps)
  const percentage = Math.round((safeActualReps / safeTargetReps) * 100)
  const diffReps = safeActualReps - safeTargetReps
  const targetSeconds = Math.round(Math.max(0.5, targetMinutes) * 60)
  const actualClock = formatSecondsClock(actualDurationSec)
  const targetClock = formatSecondsClock(targetSeconds)

  let status: TargetStatus
  if (percentage < 60) {
    status = 'far'
  } else if (percentage < 100) {
    status = 'near'
  } else if (percentage === 100 && diffReps === 0) {
    status = 'reached'
  } else {
    status = 'exceeded'
  }

  const withinTime = actualDurationSec <= targetSeconds
  const timeNote =
    lang === 'en'
      ? withinTime
        ? `Completed in ${actualClock} within your ${targetClock} target time (${completedSets}/${totalSets} sets).`
        : `Session took ${actualClock}, exceeding the ${targetClock} target time (${completedSets}/${totalSets} sets).`
      : withinTime
        ? `Selesai dalam ${actualClock} (dalam batas target ${targetClock}) · ${completedSets}/${totalSets} set.`
        : `Durasi ${actualClock} melewati target waktu ${targetClock} · ${completedSets}/${totalSets} set.`

  if (lang === 'en') {
    if (status === 'far') {
      return {
        status,
        percentage,
        targetReps: safeTargetReps,
        targetMinutes,
        actualReps: safeActualReps,
        actualDurationSec,
        completedSets,
        totalSets,
        diffReps,
        badge: 'FAR FROM TARGET',
        headline: 'Far from target',
        summary: `Completed ${safeActualReps} of ${safeTargetReps} reps (${percentage}%). You need ${Math.abs(diffReps)} more reps to hit the goal.`,
        timeNote,
      }
    }
    if (status === 'near') {
      return {
        status,
        percentage,
        targetReps: safeTargetReps,
        targetMinutes,
        actualReps: safeActualReps,
        actualDurationSec,
        completedSets,
        totalSets,
        diffReps,
        badge: 'CLOSE TO TARGET',
        headline: 'Close to target',
        summary: `Almost there! Completed ${safeActualReps} of ${safeTargetReps} reps (${percentage}%), just ${Math.abs(diffReps)} reps short.`,
        timeNote,
      }
    }
    if (status === 'reached') {
      return {
        status,
        percentage,
        targetReps: safeTargetReps,
        targetMinutes,
        actualReps: safeActualReps,
        actualDurationSec,
        completedSets,
        totalSets,
        diffReps,
        badge: 'TARGET REACHED',
        headline: 'Target reached!',
        summary: `Spot on! You completed all ${safeActualReps} of ${safeTargetReps} target reps (100%).`,
        timeNote,
      }
    }
    return {
      status,
      percentage,
      targetReps: safeTargetReps,
      targetMinutes,
      actualReps: safeActualReps,
      actualDurationSec,
      completedSets,
      totalSets,
      diffReps,
      badge: 'EXCEEDED TARGET',
      headline: 'Exceeded target!',
      summary: `Outstanding! You completed ${safeActualReps} of ${safeTargetReps} reps (${percentage}%), +${diffReps} reps above target.`,
      timeNote,
    }
  }

  if (status === 'far') {
    return {
      status,
      percentage,
      targetReps: safeTargetReps,
      targetMinutes,
      actualReps: safeActualReps,
      actualDurationSec,
      completedSets,
      totalSets,
      diffReps,
      badge: 'JAUH DARI TARGET',
      headline: 'Jauh dari target',
      summary: `Baru tercapai ${safeActualReps} dari ${safeTargetReps} reps (${percentage}%). Masih kurang ${Math.abs(diffReps)} reps lagi — tingkatkan lagi di sesi berikutnya.`,
      timeNote,
    }
  }
  if (status === 'near') {
    return {
      status,
      percentage,
      targetReps: safeTargetReps,
      targetMinutes,
      actualReps: safeActualReps,
      actualDurationSec,
      completedSets,
      totalSets,
      diffReps,
      badge: 'MENDEKATI TARGET',
      headline: 'Mendekati target',
      summary: `Sedikit lagi! Tercapai ${safeActualReps} dari ${safeTargetReps} reps (${percentage}%), tinggal ${Math.abs(diffReps)} reps lagi untuk menyentuh target.`,
      timeNote,
    }
  }
  if (status === 'reached') {
    return {
      status,
      percentage,
      targetReps: safeTargetReps,
      targetMinutes,
      actualReps: safeActualReps,
      actualDurationSec,
      completedSets,
      totalSets,
      diffReps,
      badge: 'TARGET TERCAPAI',
      headline: 'Target tercapai!',
      summary: `Tepat sasaran! Kamu berhasil menyelesaikan ${safeActualReps} dari ${safeTargetReps} reps (100%) sesuai target latihan.`,
      timeNote,
    }
  }
  return {
    status,
    percentage,
    targetReps: safeTargetReps,
    targetMinutes,
    actualReps: safeActualReps,
    actualDurationSec,
    completedSets,
    totalSets,
    diffReps,
    badge: 'MELEBIHI TARGET',
    headline: 'Melebihi target!',
    summary: `Luar biasa! Kamu menyelesaikan ${safeActualReps} dari ${safeTargetReps} reps (${percentage}%), melampaui target sebanyak +${diffReps} reps.`,
    timeNote,
  }
}
