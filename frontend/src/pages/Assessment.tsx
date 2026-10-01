import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Button } from '../components/ui/Button';
import { Card, CardContent } from '../components/ui/Card';
import { Progress } from '../components/ui/Progress';
import { ArrowRight, ArrowLeft, CheckCircle, Mic, Square, Trash2, SkipForward, AlertCircle } from 'lucide-react';
import { usePredictFused } from '../hooks/useAssessment';
import { AudioWaveformVisualizer } from '../components/tools/AudioWaveformVisualizer';
import { AudioFeatureExtractor, AudioFeatures } from '../utils/audioFeatures';

const phqQuestions = [
  "Little interest or pleasure in doing things?",
  "Feeling down, depressed, or hopeless?",
  "Trouble falling or staying asleep, or sleeping too much?",
  "Feeling tired or having little energy?",
  "Poor appetite or overeating?",
  "Feeling bad about yourself — or that you are a failure or have let yourself or your family down?",
  "Trouble concentrating on things, such as reading the newspaper or watching television?",
  "Moving or speaking so slowly that other people could have noticed? Or the opposite — being so fidgety or restless that you have been moving around a lot more than usual?",
  "Thoughts that you would be better off dead, or of hurting yourself in some way?"
];

const phqOptions = [
  { value: 0, label: 'Not at all' },
  { value: 1, label: 'Several days' },
  { value: 2, label: 'More than half the days' },
  { value: 3, label: 'Nearly every day' }
];

export default function Assessment() {
  const navigate = useNavigate();
  const [step, setStep] = useState(0);
  const [answers, setAnswers] = useState<number[]>(Array(9).fill(-1));
  const [journal, setJournal] = useState('');
  const [submitError, setSubmitError] = useState('');

  // Audio Recording State
  const [isRecording, setIsRecording] = useState(false);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [recordingSeconds, setRecordingSeconds] = useState(0);
  const [micError, setMicError] = useState('');
  const [audioSkipped, setAudioSkipped] = useState(false);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<BlobPart[]>([]);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const extractorRef = useRef<AudioFeatureExtractor>(new AudioFeatureExtractor());
  const [audioFeatures, setAudioFeatures] = useState<AudioFeatures | null>(null);
  const [activeStream, setActiveStream] = useState<MediaStream | null>(null);

  const { mutateAsync: submitAssessment, isPending } = usePredictFused();

  // Cleanup timer on unmount
  useEffect(() => {
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, []);

  const handleSelect = (val: number) => {
    const newAnswers = [...answers];
    newAnswers[step] = val;
    setAnswers(newAnswers);
    setTimeout(() => {
      if (step < 10) setStep(step + 1);
    }, 400);
  };

  const handleNext = () => { if (step < 10) setStep(step + 1); };
  const handleBack = () => { if (step > 0) setStep(step - 1); };

  const startRecording = async () => {
    setMicError('');
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        // Disable browser voice processing: automatic gain control normalises
        // loudness and would mask the RMS-based features (revision).
        audio: { autoGainControl: false, noiseSuppression: false, echoCancellation: false, channelCount: 1 },
        video: false,
      });

      // Pick best supported MIME type
      const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
        ? 'audio/webm;codecs=opus'
        : MediaRecorder.isTypeSupported('audio/webm')
        ? 'audio/webm'
        : 'audio/ogg';

      const mediaRecorder = new MediaRecorder(stream, { mimeType });
      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];
      setRecordingSeconds(0);

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };

      mediaRecorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: mimeType });
        setAudioBlob(blob);
        setAudioUrl(URL.createObjectURL(blob));
        stream.getTracks().forEach(track => track.stop());
        if (timerRef.current) clearInterval(timerRef.current);
      };

      mediaRecorder.start(250); // collect data every 250ms
      extractorRef.current.start(stream); // begin real-time acoustic feature extraction
      setActiveStream(stream);
      setIsRecording(true);

      // Start timer
      timerRef.current = setInterval(() => {
        setRecordingSeconds(s => s + 1);
      }, 1000);

    } catch (err: any) {
      if (err.name === 'NotAllowedError') {
        setMicError('Microphone access was denied. Please allow mic permissions in your browser and try again.');
      } else if (err.name === 'NotFoundError') {
        setMicError('No microphone found. Please connect a microphone and try again.');
      } else {
        setMicError('Could not start recording. Please try again.');
      }
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      setActiveStream(null);
      if (timerRef.current) clearInterval(timerRef.current);
      // Capture real acoustic features from the extractor
      const features = extractorRef.current.stop();
      setAudioFeatures(features);
    }
  };

  const deleteRecording = () => {
    setAudioBlob(null);
    setAudioFeatures(null);
    setAudioSkipped(false);
    if (audioUrl) {
      URL.revokeObjectURL(audioUrl);
      setAudioUrl(null);
    }
    setRecordingSeconds(0);
  };

  const handleSubmit = async () => {
    setSubmitError('');
    try {
      // Use real acoustic features if available
      // Revision: a skipped or unusable recording is sent as null so that the
      // server treats audio as missing and renormalises the fusion weights.
      const features = audioSkipped ? null : (audioFeatures ?? null);

      const res = await submitAssessment({
        phq: { answers },
        text: { text: journal },
        audioFeatures: features,
      });

      navigate('/results', { state: { result: res } });
    } catch (err: any) {
      console.error('Submission failed', err);
      setSubmitError('Submission failed. Please check that the backend server is running.');
    }
  };

  const formatTime = (s: number) => `${Math.floor(s / 60).toString().padStart(2, '0')}:${(s % 60).toString().padStart(2, '0')}`;

  const progress = (step / 10) * 100;
  const canSubmit = !isPending && (audioUrl !== null || audioSkipped);

  return (
    <div className="max-w-3xl mx-auto py-10">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Mental Health Assessment</h1>
        <p className="text-gray-400">Complete the multimodal screening process</p>
      </div>

      <Progress value={progress} className="h-2 mb-8 bg-white/10" indicatorClassName="bg-brand-teal" />

      <Card className="bg-white/5 border-white/10 backdrop-blur-xl min-h-[420px] flex flex-col relative overflow-hidden">
        <CardContent className="flex-1 flex flex-col p-8 md:p-12">

          <AnimatePresence mode="wait">

            {/* ── PHQ-9 Questions (steps 0–8) ──────────────────── */}
            {step < 9 && (
              <motion.div
                key={`q-${step}`}
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ duration: 0.3 }}
                className="flex-1 flex flex-col"
              >
                <span className="text-brand-amber font-medium mb-4">Question {step + 1} of 9</span>
                <h2 className="text-2xl font-semibold mb-8">{phqQuestions[step]}</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-auto">
                  {phqOptions.map((opt) => (
                    <button
                      key={opt.value}
                      onClick={() => handleSelect(opt.value)}
                      className={`p-4 rounded-xl border text-left transition-all duration-200 ${
                        answers[step] === opt.value
                          ? 'bg-brand-teal/20 border-brand-teal shadow-[0_0_15px_rgba(10,147,150,0.2)] text-white'
                          : 'bg-white/5 border-white/10 text-gray-300 hover:bg-white/10 hover:border-white/20'
                      }`}
                    >
                      {opt.label}
                    </button>
                  ))}
                </div>
              </motion.div>
            )}

            {/* ── Text Journal (step 9) ─────────────────────────── */}
            {step === 9 && (
              <motion.div
                key="journal"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ duration: 0.3 }}
                className="flex-1 flex flex-col"
              >
                <span className="text-brand-tealL font-medium mb-4">Step 10 of 11 — Text Entry</span>
                <h2 className="text-2xl font-semibold mb-4">How are you feeling right now?</h2>
                <p className="text-gray-400 mb-6">
                  Write a few sentences about your current emotional state. Our AI will analyse this alongside your questionnaire.
                </p>
                <textarea
                  className="flex-1 min-h-[160px] bg-white/5 border border-white/10 rounded-xl p-4 text-white placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-brand-teal/50 resize-none"
                  placeholder="I've been feeling..."
                  value={journal}
                  onChange={(e) => setJournal(e.target.value)}
                />
                <p className="text-xs text-gray-500 mt-2 text-right">{journal.length} characters (min 10)</p>
              </motion.div>
            )}

            {/* ── Voice Recording (step 10) ─────────────────────── */}
            {step === 10 && (
              <motion.div
                key="audio"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ duration: 0.3 }}
                className="flex-1 flex flex-col"
              >
                <span className="text-purple-400 font-medium mb-4">Step 11 of 11 — Voice Analysis</span>
                <h2 className="text-2xl font-semibold mb-2">Speak freely for 10–30 seconds</h2>
                <p className="text-gray-400 mb-6 text-sm">
                  Describe how you have been feeling lately. Our acoustic AI will analyse tone, pitch, and speech patterns. You can also skip this step.
                </p>

                <div className="flex-1 flex flex-col items-center justify-center gap-6 bg-white/5 border border-white/10 rounded-xl p-8">

                  {/* Mic error */}
                  {micError && (
                    <div className="flex items-start gap-3 bg-red-500/10 border border-red-500/20 rounded-xl p-4 w-full max-w-md">
                      <AlertCircle className="w-5 h-5 text-red-400 mt-0.5 flex-shrink-0" />
                      <p className="text-red-300 text-sm">{micError}</p>
                    </div>
                  )}

                  {/* Before recording */}
                  {!audioUrl && !audioSkipped && (
                    <>
                      {/* Animated mic ring */}
                      <div className={`relative w-32 h-32 rounded-full flex items-center justify-center ${isRecording ? '' : ''}`}>
                        {isRecording && (
                          <>
                            <span className="absolute inset-0 rounded-full bg-red-500/20 animate-ping" />
                            <span className="absolute inset-2 rounded-full bg-red-500/10 animate-pulse" />
                          </>
                        )}
                        <button
                          onClick={isRecording ? stopRecording : startRecording}
                          className={`relative z-10 w-24 h-24 rounded-full flex items-center justify-center text-white transition-all shadow-lg hover:scale-105 active:scale-95 ${
                            isRecording ? 'bg-red-500 hover:bg-red-600' : 'bg-brand-teal hover:bg-teal-600'
                          }`}
                        >
                          {isRecording ? <Square className="w-8 h-8" /> : <Mic className="w-8 h-8" />}
                        </button>
                      </div>

                      <div className="text-center">
                        {isRecording ? (
                          <>
                            <p className="text-red-400 font-semibold text-lg mb-2">Recording — {formatTime(recordingSeconds)}</p>
                            <AudioWaveformVisualizer isRecording={isRecording} stream={activeStream} />
                            <p className="text-gray-500 text-sm mt-3">Click the button to stop</p>
                          </>
                        ) : (
                          <>
                            <p className="text-gray-300 font-medium">Click to start recording</p>
                            <p className="text-gray-500 text-sm mt-1">Aim for 10–30 seconds</p>
                          </>
                        )}
                      </div>
                    </>
                  )}

                  {/* After recording — playback */}
                  {audioUrl && !audioSkipped && (
                    <div className="w-full flex flex-col items-center gap-5">
                      <div className="w-12 h-12 rounded-full bg-green-500/20 flex items-center justify-center">
                        <CheckCircle className="w-6 h-6 text-green-400" />
                      </div>
                      <p className="text-green-400 font-semibold">Recording complete — {formatTime(recordingSeconds)}</p>
                      <audio src={audioUrl} controls className="w-full max-w-sm rounded-xl" />
                      <Button variant="outline" onClick={deleteRecording} className="text-red-400 border-red-400/20 hover:bg-red-400/10 text-sm">
                        <Trash2 className="w-4 h-4 mr-2" />
                        Delete & Retake
                      </Button>
                    </div>
                  )}

                  {/* Skipped state */}
                  {audioSkipped && (
                    <div className="flex flex-col items-center gap-4 text-center">
                      <p className="text-gray-400">Voice step skipped. The assessment will use text + PHQ-9 only.</p>
                      <Button variant="outline" onClick={() => setAudioSkipped(false)} className="text-gray-400 text-sm">
                        Go back and record
                      </Button>
                    </div>
                  )}
                </div>

                {/* Skip option */}
                {!audioSkipped && !audioUrl && (
                  <button
                    onClick={() => { setAudioSkipped(true); setMicError(''); }}
                    className="mt-4 text-sm text-gray-500 hover:text-gray-300 flex items-center gap-1 mx-auto transition-colors"
                  >
                    <SkipForward className="w-3 h-3" />
                    Skip voice recording
                  </button>
                )}

                {/* Submit error */}
                {submitError && (
                  <div className="mt-4 flex items-center gap-2 bg-red-500/10 border border-red-500/20 rounded-xl px-4 py-3">
                    <AlertCircle className="w-4 h-4 text-red-400" />
                    <p className="text-red-300 text-sm">{submitError}</p>
                  </div>
                )}
              </motion.div>
            )}

          </AnimatePresence>

          {/* ── Navigation ───────────────────────────────────────── */}
          <div className="flex justify-between items-center mt-10 pt-6 border-t border-white/10">
            <Button
              variant="outline"
              onClick={handleBack}
              disabled={step === 0 || isPending || isRecording}
              className="border-white/10 text-gray-300 hover:bg-white/5"
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back
            </Button>

            {step < 9 && (
              <Button onClick={handleNext} disabled={answers[step] === -1} className="bg-brand-teal hover:bg-teal-600 text-white">
                Next <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            )}

            {step === 9 && (
              <Button onClick={handleNext} disabled={journal.length < 10} className="bg-brand-teal hover:bg-teal-600 text-white">
                Continue to Voice <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            )}

            {step === 10 && (
              <Button
                onClick={handleSubmit}
                disabled={!canSubmit || isRecording}
                className="bg-brand-amber hover:bg-yellow-500 text-[#0D1B2A] font-bold"
              >
                {isPending ? 'Analysing...' : 'Submit Assessment'}
                {!isPending && <CheckCircle className="w-4 h-4 ml-2" />}
              </Button>
            )}
          </div>

        </CardContent>
      </Card>
    </div>
  );
}
