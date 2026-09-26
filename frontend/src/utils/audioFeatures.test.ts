import assert from 'node:assert/strict';
import test from 'node:test';

import { buildAudioFeatures } from './audioFeatures.ts';

test('no frames are represented as missing audio', () => {
  assert.equal(buildAudioFeatures([], [], [], [], 0, 0), null);
});

test('fewer than five frames are represented as missing audio', () => {
  const values = [0.1, 0.2, 0.3, 0.4];
  assert.equal(buildAudioFeatures(values, values, values, values, 3, 4), null);
});

test('no audio and very-short audio use the same missing-modality representation', () => {
  const values = [0.1, 0.2, 0.3, 0.4];
  const skipped = buildAudioFeatures([], [], [], [], 0, 0);
  const veryShort = buildAudioFeatures(values, values, values, values, 3, 4);
  assert.equal(veryShort, skipped);
});

test('five valid frames produce the six supplied audio descriptors', () => {
  const features = buildAudioFeatures(
    [0.1, 0.2, 0.3, 0.4, 0.5],
    [0.1, 0.1, 0.2, 0.2, 0.3],
    [0.2, 0.3, 0.4, 0.5, 0.6],
    [0.3, 0.4, 0.5, 0.6, 0.7],
    4,
    5,
  );

  assert.notEqual(features, null);
  assert.deepEqual(Object.keys(features!).sort(), [
    'rms_mean',
    'rms_std',
    'speaking_ratio',
    'spectral_centroid',
    'spectral_rolloff',
    'zcr_mean',
  ]);
  assert.equal(features!.speaking_ratio, 0.8);
});
