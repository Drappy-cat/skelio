import { useState } from 'react'
import {
  DifficultyLevel,
  EXERCISE_RECOMMENDATIONS,
  ExerciseKind,
  ExerciseRecommendation,
  TrainingPlan,
  TrainingSet,
  distributeRepsAcrossSets,
  estimatePlanMinutes,
  getPlanTotalReps,
} from './trainingPlan'

export function TrainingPlanScreen({
  plans,
  activePlanId,
  onSaveAndStart,
  onSelectPlan,
  onCreateNewPlan,
  onBack,
  lang,
}: {
  plans: TrainingPlan[]
  activePlanId: string
  onSaveAndStart: (plan: TrainingPlan) => void
  onSelectPlan: (planId: string) => void
  onCreateNewPlan: (plan: TrainingPlan) => void
  onBack: () => void
  lang: 'id' | 'en'
}) {
  const current = plans.find((p) => p.id === activePlanId) || plans[0]
  const [draft, setDraft] = useState<TrainingPlan>(() => ({
    ...current,
    sets: current.sets.map((s) => ({ ...s })),
  }))
  const [manualMinutes, setManualMinutes] = useState(false)
  const [creatingNewPlan, setCreatingNewPlan] = useState(false)
  const [newPlanName, setNewPlanName] = useState('')

  const isEn = lang === 'en'
  const totalReps = getPlanTotalReps(draft)

  const handleChooseSavedPlan = (plan: TrainingPlan) => {
    onSelectPlan(plan.id)
    setManualMinutes(false)
    setCreatingNewPlan(false)
    setDraft({
      ...plan,
      sets: plan.sets.map((s) => ({ ...s })),
    })
  }

  const handleSwitchExerciseTab = (ex: ExerciseKind) => {
    if (draft.exercise === ex) return
    setCreatingNewPlan(false)
    const existing = plans.find((p) => p.exercise === ex)
    if (existing) {
      handleChooseSavedPlan(existing)
      return
    }
    const rec = EXERCISE_RECOMMENDATIONS[ex][1]
    const created: TrainingPlan = {
      id: `plan-${ex.toLowerCase()}-${Date.now()}`,
      name: `${ex} Target`,
      description: rec.description,
      exercise: ex,
      difficulty: rec.difficulty,
      targetMinutes: rec.targetMinutes,
      sets: rec.sets.map((s, idx) => ({
        id: `set-${Date.now()}-${idx}`,
        reps: s.reps,
        restSeconds: s.restSeconds,
      })),
    }
    onCreateNewPlan(created)
    setManualMinutes(false)
    setDraft(created)
  }

  const openNewPlanCreator = () => {
    setNewPlanName('')
    setCreatingNewPlan((prev) => !prev)
  }

  const confirmNewBlankPlan = () => {
    const customName = newPlanName.trim() || `${draft.exercise} ${isEn ? 'Custom' : 'Kustom'}`
    const initialSets: TrainingSet[] = [
      { id: `set-${Date.now()}-1`, reps: 20, restSeconds: 30 },
      { id: `set-${Date.now()}-2`, reps: 15, restSeconds: 30 },
      { id: `set-${Date.now()}-3`, reps: 15, restSeconds: 30 },
    ]
    const fresh: TrainingPlan = {
      id: `plan-${Date.now()}`,
      name: customName,
      description: '',
      exercise: draft.exercise,
      difficulty: 'Intermediate',
      targetMinutes: estimatePlanMinutes(initialSets),
      sets: initialSets,
    }
    onCreateNewPlan(fresh)
    setManualMinutes(false)
    setCreatingNewPlan(false)
    setNewPlanName('')
    setDraft(fresh)
  }

  const updateSets = (nextSets: TrainingSet[]) => {
    setDraft((prev) => ({
      ...prev,
      customTotalReps: undefined,
      sets: nextSets,
      targetMinutes: manualMinutes ? prev.targetMinutes : estimatePlanMinutes(nextSets),
    }))
  }

  const updateCustomTotal = (nextTotal: number) => {
    const safeTotal = Math.max(1, Math.min(2000, Math.round(nextTotal)))
    setDraft((prev) => ({
      ...prev,
      customTotalReps: safeTotal,
      targetMinutes: manualMinutes
        ? prev.targetMinutes
        : estimatePlanMinutes(prev.sets, safeTotal),
    }))
  }

  const updateSet = (index: number, patch: Partial<TrainingSet>) => {
    const nextSets = draft.sets.map((s, i) => (i === index ? { ...s, ...patch } : s))
    updateSets(nextSets)
  }

  const addSet = () => {
    const lastReps = draft.sets[draft.sets.length - 1]?.reps ?? 15
    const lastRest = draft.sets[draft.sets.length - 1]?.restSeconds ?? 30
    updateSets([
      ...draft.sets,
      { id: `set-${Date.now()}-${draft.sets.length + 1}`, reps: lastReps, restSeconds: lastRest },
    ])
  }

  const removeSet = (index: number) => {
    if (draft.sets.length <= 1) return
    updateSets(draft.sets.filter((_, i) => i !== index))
  }

  const setSetCount = (nextCount: number) => {
    const count = Math.max(1, Math.min(20, Math.round(nextCount)))
    if (count === draft.sets.length) return
    if (count < draft.sets.length) {
      updateSets(draft.sets.slice(0, count))
      return
    }
    const lastReps = draft.sets[draft.sets.length - 1]?.reps ?? 15
    const lastRest = draft.sets[draft.sets.length - 1]?.restSeconds ?? 30
    const extraSets: TrainingSet[] = Array.from({ length: count - draft.sets.length }, (_, i) => ({
      id: `set-${Date.now()}-${draft.sets.length + i + 1}`,
      reps: lastReps,
      restSeconds: lastRest,
    }))
    updateSets([...draft.sets, ...extraSets])
  }

  const equalizeSets = () => {
    const first = draft.sets[0]
    if (!first) return
    updateSets(
      draft.sets.map((s) => ({
        ...s,
        reps: first.reps,
        restSeconds: first.restSeconds,
      })),
    )
  }

  const applyRecommendation = (rec: ExerciseRecommendation) => {
    setManualMinutes(false)
    setDraft((prev) => ({
      ...prev,
      exercise: rec.exercise,
      difficulty: rec.difficulty,
      targetMinutes: rec.targetMinutes,
      customTotalReps: undefined,
      description: rec.description,
      sets: rec.sets.map((s, idx) => ({
        id: `rec-${Date.now()}-${idx}`,
        reps: s.reps,
        restSeconds: s.restSeconds,
      })),
    }))
  }

  const exercises: ExerciseKind[] = ['Push-up', 'Squat', 'Sit-up']
  const difficulties: DifficultyLevel[] = ['Beginner', 'Intermediate', 'Advanced']
  const currentRecommendations = EXERCISE_RECOMMENDATIONS[draft.exercise]
  const plansForExercise = plans.filter((p) => p.exercise === draft.exercise)

  return (
    <div className="detail-screen plan-screen">
      <div className="detail-header plan-topbar">
        <button className="round-back" onClick={onBack} aria-label="Kembali">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round">
            <path d="m15 18-6-6 6-6" />
          </svg>
        </button>
        <div>
          <span>{isEn ? 'WORKOUT CUSTOMIZATION' : 'KUSTOMISASI LATIHAN'}</span>
          <h1>{isEn ? 'Training Target Plan' : 'Atur Target Latihan'}</h1>
        </div>
      </div>

      {/* Top Exercise Tabs + Saved Plan Pills */}
      <div className="plan-scroll">
      <div className="plan-exercise-tabs" role="tablist" aria-label={isEn ? 'Choose exercise' : 'Pilih olahraga'}>
        {exercises.map((ex) => (
          <button
            key={ex}
            type="button"
            role="tab"
            aria-selected={draft.exercise === ex}
            className={draft.exercise === ex ? 'active' : ''}
            onClick={() => handleSwitchExerciseTab(ex)}
          >
            {ex}
          </button>
        ))}
      </div>

      <div className="plan-pill-row">
        {plansForExercise.map((p) => (
          <button
            key={p.id}
            type="button"
            className={`plan-pill ${p.id === draft.id ? 'active' : ''}`}
            onClick={() => handleChooseSavedPlan(p)}
          >
            {p.name}
          </button>
        ))}
        <button type="button" className={`plan-pill add ${creatingNewPlan ? 'active' : ''}`} onClick={openNewPlanCreator}>
          + {isEn ? 'New Plan' : 'Plan Baru'}
        </button>
      </div>

      {creatingNewPlan && (
        <form
          className="plan-new-form"
          onSubmit={(e) => {
            e.preventDefault()
            confirmNewBlankPlan()
          }}
        >
          <input
            type="text"
            value={newPlanName}
            onChange={(e) => setNewPlanName(e.target.value)}
            placeholder={isEn ? `Plan name (e.g. Morning ${draft.exercise})` : `Nama plan (misal: ${draft.exercise} Pagi)`}
            maxLength={40}
            autoFocus
            aria-label={isEn ? 'New plan name' : 'Nama plan baru'}
          />
          <button type="submit" className="plan-new-save">
            {isEn ? 'Create' : 'Buat'}
          </button>
          <button type="button" className="plan-new-cancel" onClick={() => setCreatingNewPlan(false)}>
            {isEn ? 'Cancel' : 'Batal'}
          </button>
        </form>
      )}

      {/* Hero Summary Card (matching reference screenshot) */}
      <section className="plan-hero-card">
        <div className="plan-hero-kicker-row">
          <span className="plan-hero-kicker">TOTAL</span>
          {typeof draft.customTotalReps === 'number' && (
            <div className="plan-total-helpers">
              <button
                type="button"
                className="plan-auto-min"
                onClick={() =>
                  setDraft((prev) => ({
                    ...prev,
                    customTotalReps: undefined,
                    sets: distributeRepsAcrossSets(totalReps, prev.sets),
                  }))
                }
              >
                {isEn ? 'Sync to Sets' : 'Bagi ke Set'}
              </button>
              <button
                type="button"
                className="plan-auto-min"
                onClick={() =>
                  setDraft((prev) => ({
                    ...prev,
                    customTotalReps: undefined,
                    targetMinutes: manualMinutes
                      ? prev.targetMinutes
                      : estimatePlanMinutes(prev.sets),
                  }))
                }
              >
                (Auto)
              </button>
            </div>
          )}
        </div>
        <div className="plan-hero-total">
          <div className="plan-total-inline">
            <button
              type="button"
              aria-label="Kurangi total target"
              onClick={() => updateCustomTotal(totalReps - 1)}
            >
              −
            </button>
            <input
              type="number"
              min={1}
              max={2000}
              value={totalReps}
              onChange={(e) => {
                const v = parseInt(e.target.value, 10)
                updateCustomTotal(Number.isFinite(v) && v >= 1 ? v : 1)
              }}
              aria-label="Total target reps"
            />
            <button
              type="button"
              aria-label="Tambah total target"
              onClick={() => updateCustomTotal(totalReps + 1)}
            >
              +
            </button>
          </div>
          <span>{draft.exercise.toLowerCase()}s</span>
        </div>

        <div className="plan-hero-divider" />

        <div className="plan-hero-stats">
          <div>
            <small>{isEn ? 'TRAINING SETS' : 'TRAINING SETS'}</small>
            <div className="plan-minutes-inline">
              <button
                type="button"
                aria-label="Kurangi jumlah set"
                onClick={() => setSetCount(draft.sets.length - 1)}
                disabled={draft.sets.length <= 1}
              >
                −
              </button>
              <input
                type="number"
                min={1}
                max={20}
                value={draft.sets.length}
                onChange={(e) => {
                  const val = parseInt(e.target.value, 10)
                  if (Number.isFinite(val) && val >= 1) {
                    setSetCount(val)
                  }
                }}
                aria-label="Jumlah training sets"
              />
              <button
                type="button"
                aria-label="Tambah jumlah set"
                onClick={() => setSetCount(draft.sets.length + 1)}
                disabled={draft.sets.length >= 20}
              >
                +
              </button>
            </div>
          </div>
          <div>
            <small>
              {isEn ? 'MINUTES' : 'MINUTES'}{' '}
              {manualMinutes && (
                <button
                  type="button"
                  className="plan-auto-min"
                  onClick={() => {
                    setManualMinutes(false)
                    setDraft((prev) => ({ ...prev, targetMinutes: estimatePlanMinutes(prev.sets) }))
                  }}
                >
                  (Auto)
                </button>
              )}
            </small>
            <div className="plan-minutes-inline">
              <button
                type="button"
                aria-label="Kurangi menit"
                onClick={() => {
                  setManualMinutes(true)
                  setDraft((prev) => ({
                    ...prev,
                    targetMinutes: Math.max(0.5, Number((prev.targetMinutes - 0.5).toFixed(1))),
                  }))
                }}
              >
                −
              </button>
              <input
                type="number"
                step="0.5"
                min="0.5"
                max="120"
                value={draft.targetMinutes}
                onChange={(e) => {
                  const val = parseFloat(e.target.value)
                  setManualMinutes(true)
                  setDraft((prev) => ({
                    ...prev,
                    targetMinutes: Number.isFinite(val) && val > 0 ? val : 0.5,
                  }))
                }}
                aria-label="Target menit"
              />
              <button
                type="button"
                aria-label="Tambah menit"
                onClick={() => {
                  setManualMinutes(true)
                  setDraft((prev) => ({
                    ...prev,
                    targetMinutes: Math.min(120, Number((prev.targetMinutes + 0.5).toFixed(1))),
                  }))
                }}
              >
                +
              </button>
            </div>
          </div>
        </div>

        <button
          type="button"
          className="plan-cta-button"
          onClick={() =>
            onSaveAndStart({
              ...draft,
              name: draft.name.trim() || `${draft.exercise} ${totalReps}`,
            })
          }
        >
          ✓ {isEn ? 'Save & Start Workout' : 'Simpan & Mulai Latihan'}
        </button>
      </section>

      {/* Plan Info Card */}
      <section className="plan-card">
        <div className="plan-label-row">
          <span className="plan-label">{isEn ? 'EXERCISE TYPE' : 'JENIS OLAHRAGA'}</span>
          <span className="plan-active-ex-pill">{draft.exercise}</span>
        </div>

        <div className="plan-rec-wrap">
          <span className="plan-label">
            {isEn
              ? `RECOMMENDED ${draft.exercise.toUpperCase()} TARGETS (EDITABLE)`
              : `REKOMENDASI ${draft.exercise.toUpperCase()} (BISA DIEDIT)`}
          </span>
          <div className="plan-rec-row">
            {currentRecommendations.map((rec) => {
              const recTotal = rec.sets.reduce((sum, s) => sum + s.reps, 0)
              const isMatch =
                draft.customTotalReps === undefined &&
                totalReps === recTotal &&
                draft.sets.length === rec.sets.length &&
                draft.difficulty === rec.difficulty
              return (
                <button
                  key={rec.id}
                  type="button"
                  className={`plan-rec-chip ${isMatch ? 'active' : ''}`}
                  onClick={() => applyRecommendation(rec)}
                >
                  <b>{rec.label}</b>
                  <small>
                    {rec.sets.map((s) => s.reps).join('+')} · {rec.targetMinutes} {isEn ? 'min' : 'mnt'}
                  </small>
                </button>
              )
            })}
          </div>
        </div>

        <label className="plan-field">
          <span>PLAN NAME</span>
          <div className="plan-input-box">
            <i className="plan-input-icon">T</i>
            <input
              type="text"
              value={draft.name}
              onChange={(e) => setDraft((prev) => ({ ...prev, name: e.target.value }))}
              placeholder="Ultimate"
            />
          </div>
        </label>

        <label className="plan-field">
          <span>DESCRIPTION (OPTIONAL)</span>
          <div className="plan-input-box active-outline">
            <i className="plan-input-icon">≡</i>
            <input
              type="text"
              value={draft.description}
              onChange={(e) => setDraft((prev) => ({ ...prev, description: e.target.value }))}
              placeholder="Intense Push Up Challenge"
            />
          </div>
        </label>

        <div className="plan-diff-wrap">
          <span className="plan-label">DIFFICULTY LEVEL</span>
          <div className="plan-diff-row">
            {difficulties.map((lv) => (
              <button
                key={lv}
                type="button"
                className={draft.difficulty === lv ? 'active' : ''}
                onClick={() => setDraft((prev) => ({ ...prev, difficulty: lv }))}
              >
                {lv === 'Intermediate' ? 'Inter.' : lv}
              </button>
            ))}
          </div>
        </div>
      </section>

      {/* Training Sets Card */}
      <section className="plan-card">
        <div className="plan-sets-head">
          <span className="plan-label">TRAINING SETS</span>
          <div className="plan-sets-actions">
            {draft.sets.length > 1 && (
              <button
                type="button"
                className="plan-sync-set"
                onClick={equalizeSets}
                title={isEn ? 'Match all sets to Set 1' : 'Samakan semua set seperti Set 1'}
              >
                {isEn ? 'Match Set 1' : 'Samakan Set'}
              </button>
            )}
            <button type="button" className="plan-add-set" onClick={addSet}>
              + {isEn ? 'Add Set' : 'Add Set'}
            </button>
          </div>
        </div>

        <div className="plan-sets-list">
          {draft.sets.map((s, idx) => (
            <div className="plan-set-item" key={s.id}>
              <div className="plan-set-top">
                <b>Set {idx + 1}</b>
                {draft.sets.length > 1 && (
                  <button
                    type="button"
                    className="plan-del-set"
                    onClick={() => removeSet(idx)}
                    aria-label={`Hapus Set ${idx + 1}`}
                    title={isEn ? 'Remove set' : 'Hapus set'}
                  >
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M3 6h18" />
                      <path d="M8 6V4h8v2" />
                      <path d="M6 6l1 14h10l1-14" />
                    </svg>
                  </button>
                )}
              </div>
              <div className="plan-set-controls">
                <div>
                  <small>{draft.exercise.toUpperCase()}S:</small>
                  <div className="stepper">
                    <button
                      type="button"
                      onClick={() => updateSet(idx, { reps: Math.max(1, s.reps - 1) })}
                    >
                      −
                    </button>
                    <input
                      type="number"
                      min={1}
                      max={300}
                      value={s.reps}
                      onChange={(e) => {
                        const v = parseInt(e.target.value, 10)
                        updateSet(idx, { reps: Number.isFinite(v) && v >= 1 ? Math.min(300, v) : 1 })
                      }}
                      aria-label={`Set ${idx + 1} reps`}
                    />
                    <button
                      type="button"
                      onClick={() => updateSet(idx, { reps: Math.min(300, s.reps + 1) })}
                    >
                      +
                    </button>
                  </div>
                </div>
                <div>
                  <small>REST (SEC):</small>
                  <div className="stepper">
                    <button
                      type="button"
                      onClick={() => updateSet(idx, { restSeconds: Math.max(0, s.restSeconds - 5) })}
                    >
                      −
                    </button>
                    <input
                      type="number"
                      min={0}
                      max={300}
                      value={s.restSeconds}
                      onChange={(e) => {
                        const v = parseInt(e.target.value, 10)
                        updateSet(idx, {
                          restSeconds: Number.isFinite(v) && v >= 0 ? Math.min(300, v) : 0,
                        })
                      }}
                      aria-label={`Set ${idx + 1} rest seconds`}
                    />
                    <button
                      type="button"
                      onClick={() => updateSet(idx, { restSeconds: Math.min(300, s.restSeconds + 5) })}
                    >
                      +
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>
      </div>
    </div>
  )
}
