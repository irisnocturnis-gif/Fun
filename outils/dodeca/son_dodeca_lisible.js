/* =====================================================================
   SON DE LA CINÉMATIQUE DU DODÉCAÈDRE — version lisible
   Même son que dodeca-test.html (mêmes valeurs, même ordre des bruits
   aléatoires). Seule la mise en forme et les commentaires changent.

   COMMENT LIRE
   - Tous les temps sont en secondes depuis le début de la cinématique (0 à 40 s).
   - "volume" : 0 = silence, 1 = volume maximum d'une couche seule.
     Les couches s'additionnent, donc plusieurs couches à 0,3 en même
     temps peuvent dépasser 1 avant le volume final.
   - Pour trouver une couche qui gêne : baisse son volume (ou mets 0).
   ===================================================================== */


/* ---------------------------------------------------------------------
   1. RÉGLAGES GÉNÉRAUX
   --------------------------------------------------------------------- */
const MASTER      = 0.5;   // volume général de la cinématique
const MAKEUP_GAIN = 0.9;   // petit gain appliqué après le compresseur
const PHONE_GAIN  = 0.6;   // le mode téléphone multiplie le volume par 0,6
const DUREE       = 40;    // durée totale du son (s)
const FIN_FADE    = 38;    // le volume général commence à descendre ici, jusqu'à 40 s


/* ---------------------------------------------------------------------
   2. CHAÎNE FINALE (tout le son passe ici avant les enceintes)

   couches sonores → bus → coupe-bas → compresseur → gain final → sortie

   - coupe-bas : retire les graves (85 Hz, ou 150 Hz en mode téléphone)
   - compresseur : réduit l'écart entre sons faibles et forts.
     C'est le réglage le plus "serré" : ratio 14 = très fort,
     attaque 3 ms = réagit presque instantanément.
   - ?mix=1 dans l'adresse : sans compresseur
   - ?mix=2 dans l'adresse : compresseur doux
   --------------------------------------------------------------------- */
function masterChain(c, out) {
  const bus = c.createGain();
  const hp  = c.createBiquadFilter();           // coupe-bas
  const cp  = c.createDynamicsCompressor();     // compresseur
  const mk  = c.createGain();                   // gain final

  hp.type = 'highpass';
  hp.frequency.value = phoneMode ? 150 : 85;
  hp.Q.value = 0.7;

  const MIX = new URLSearchParams(location.search).get('mix') || '';

  // Compresseur normal
  cp.threshold.value = -20;   // il agit au-dessus de -20 dB
  cp.knee.value      = 10;
  cp.ratio.value     = 14;    // fort : quasi limiteur
  cp.attack.value    = 0.003; // 3 ms
  cp.release.value   = 0.25;

  // Variante douce (?mix=2)
  if (MIX === '2') {
    cp.threshold.value = -12;
    cp.knee.value      = 24;
    cp.ratio.value     = 3;
    cp.attack.value    = 0.02;
    cp.release.value   = 0.3;
  }

  mk.gain.value = MAKEUP_GAIN * (phoneMode ? PHONE_GAIN : 1);

  bus.connect(hp);
  if (MIX === '1') {            // sans compresseur
    hp.connect(mk);
  } else {
    hp.connect(cp);
    cp.connect(mk);
  }
  mk.connect(out);

  return { bus, hp, mk };
}


/* ---------------------------------------------------------------------
   3. OUTIL : bruit blanc de départ (2 s, toujours le même)
   --------------------------------------------------------------------- */
function mkNoise(actx) {
  const len = actx.sampleRate * 2;
  const b = actx.createBuffer(1, len, actx.sampleRate);
  const d = b.getChannelData(0);
  let q = 12345;
  for (let i = 0; i < len; i++) {
    q = (q * 1664525 + 1013904223) >>> 0;
    d[i] = (q / 4294967296) * 2 - 1;
  }
  return b;
}


/* ---------------------------------------------------------------------
   4. LE SON : toutes les couches, dans l'ordre de la cinématique
   --------------------------------------------------------------------- */
function buildSound(actx, dest, t0) {
  const noise = mkNoise(actx);

  // Hasard reproductible (donne toujours les mêmes "tirages")
  let sd = 777;
  const rnd = () => {
    sd = (sd * 1664525 + 1013904223) >>> 0;
    return sd / 4294967296;
  };

  /* ---- Outil A : un son musical (sinus, dent de scie…) ----------------
     osc(forme, freqDébut, freqFin, début, fin, volume, montée, descente, sortie)
       forme       : 'sine' (doux), 'sawtooth' (rugueux, riche en harmoniques)
       freqDébut/Fin : la hauteur glisse de l'une à l'autre (Hz)
       débutDébut/fin : quand le son commence et finit (s)
       montée      : durée pour atteindre le volume (s)
       descente    : durée pour redescendre à la fin (s)               */
  function osc(type, f0, f1, ta, tb, vol, att, rel, out) {
    const o  = actx.createOscillator();
    const gn = actx.createGain();
    o.type = type;
    o.frequency.setValueAtTime(f0, t0 + ta);
    if (f1 !== f0) o.frequency.exponentialRampToValueAtTime(f1, t0 + tb);

    const finMontee = t0 + ta + att;
    const debutDescente = Math.max(finMontee, t0 + tb - rel);
    gn.gain.setValueAtTime(0.0001, t0 + ta);
    gn.gain.linearRampToValueAtTime(vol, finMontee);
    gn.gain.setValueAtTime(vol, debutDescente);
    gn.gain.linearRampToValueAtTime(0.0001, t0 + tb);

    o.connect(gn);
    gn.connect(out || dest);
    o.start(t0 + ta);
    o.stop(t0 + tb + 0.05);
  }

  /* ---- Outil B : un souffle / crépitement (bruit filtré) --------------
     burst(début, durée, filtre, freqDébut, freqFin, volume, Q, sortie)
       filtre : 'lowpass' (garde les graves), 'highpass' (garde les aigus),
                'bandpass' (garde une bande étroite)
       Q      : plus il est grand, plus la bande est étroite et "sifflante" */
  function burst(ta, dur, ft, f0, f1, vol, Q, out) {
    const src = actx.createBufferSource();
    const fl  = actx.createBiquadFilter();
    const gn  = actx.createGain();
    src.buffer = noise;
    fl.type = ft;
    fl.Q.value = Q || 1;
    fl.frequency.setValueAtTime(f0, t0 + ta);
    if (f1 !== f0) fl.frequency.exponentialRampToValueAtTime(f1, t0 + ta + dur);
    gn.gain.setValueAtTime(vol, t0 + ta);
    gn.gain.exponentialRampToValueAtTime(0.0001, t0 + ta + dur);
    src.connect(fl);
    fl.connect(gn);
    gn.connect(out || dest);
    src.start(t0 + ta, rnd() * 1.5);
    src.stop(t0 + ta + dur + 0.05);
  }

  /* ---- Réverbération (écho de salle, 4 s) ---------------------------- */
  const rv = actx.createConvolver();
  const LN = actx.sampleRate * 4;
  const ir = actx.createBuffer(2, LN, actx.sampleRate);
  for (let ch = 0; ch < 2; ch++) {
    const d = ir.getChannelData(ch);
    for (let i = 0; i < LN; i++) d[i] = (rnd() * 2 - 1) * Math.pow(1 - i / LN, 2.4);
  }
  rv.buffer = ir;
  const wet = actx.createGain();
  wet.gain.value = 0.75;            // quantité de réverbération
  rv.connect(wet);
  wet.connect(dest);

  // "sx" = sortie avec réverbération (sert aux sons de cristal)
  const sx = actx.createGain();
  sx.connect(dest);
  sx.connect(rv);

  // Place un son à gauche (-1) ou à droite (+1) ; renvoie l'entrée à utiliser
  const pan = v => {
    const p = actx.createStereoPanner();
    p.pan.value = v;
    p.connect(sx);
    return p;
  };


  /* ===================================================================
     COUCHE 1 — 0 à 14 s : nappe aérienne (deux notes très douces)
     =================================================================== */
  osc('sine', 110,   110,   0, 14, 0.05, 3, 3);    // volume 0,05
  osc('sine', 164.8, 164.8, 0, 14, 0.03, 4, 3);    // volume 0,03

  // (3 à 10,5 s : les tintements par pentagone ont été retirés pour le moment)


  /* ===================================================================
     COUCHE 2 — 10,5 à 29 s : bourdon qui monte avec la sphère
     La dent de scie passe par un filtre qui s'ouvre peu à peu (180 → 3000 Hz).
     =================================================================== */
  const lp = actx.createBiquadFilter();
  lp.type = 'lowpass';
  lp.frequency.setValueAtTime(180, t0 + 10.5);
  lp.frequency.exponentialRampToValueAtTime(3000, t0 + 26);
  lp.connect(dest);

  osc('sawtooth', 55,   55,   10.5, 29, 0.15, 4, 3, lp);   // grave rugueux, volume 0,15
  osc('sawtooth', 55.6, 55.6, 10.5, 29, 0.13, 4, 3, lp);   // légèrement désaccordé, 0,13
  osc('sine',     110,  440,  10.5, 26, 0.12, 3, 3);       // note qui monte, 0,12
  osc('sine',     1760, 3520, 14,   26, 0.014, 4, 3);      // aigu qui monte, très discret


  /* ===================================================================
     COUCHE 3 — 12,5 à 27 s : crépitement des dragons (150 petits claquements)
     Plus on avance, plus ils sont nombreux et forts. Volume max ≈ 0,07.
     =================================================================== */
  for (let k = 0; k < 150; k++) {
    const ta = 12.5 + Math.pow(rnd(), 0.6) * 14.5;
    const volume = 0.07 * (0.3 + 0.7 * Math.min(1, (ta - 12) / 14));
    burst(ta, 0.04, 'bandpass', 3000 + rnd() * 3000, 3000 + rnd() * 3000, volume, 4);
  }


  /* ===================================================================
     COUCHE 4 — 20,5 à 36 s : trou noir (grave profond + souffle montant)
     =================================================================== */
  osc('sine', 46, 30, 20.5, 36, 0.3, 5, 8);        // grave très bas, volume 0,3

  // Souffle qui monte de 22 à 27,5 s puis s'éteint à 29,5 s (volume max 0,22)
  {
    const src = actx.createBufferSource();
    const fl  = actx.createBiquadFilter();
    const gn  = actx.createGain();
    src.buffer = noise;
    src.loop = true;
    fl.type = 'lowpass';
    fl.frequency.setValueAtTime(200, t0 + 22);
    fl.frequency.exponentialRampToValueAtTime(5000, t0 + 27.5);
    gn.gain.setValueAtTime(0.0001, t0 + 22);
    gn.gain.linearRampToValueAtTime(0.22, t0 + 27.5);
    gn.gain.linearRampToValueAtTime(0.0001, t0 + 29.5);
    src.connect(fl);
    fl.connect(gn);
    gn.connect(dest);
    src.start(t0 + 22);
    src.stop(t0 + 29.6);
  }


  /* ===================================================================
     COUCHE 5 — 28,6 à 34 s : onde de choc
     =================================================================== */
  osc('sine', 70, 26, 28.6, 34, 0.5, 0.02, 4.5);                // grave puissant, volume 0,5
  burst(28.6, 3.5, 'lowpass', 900, 150, 0.35, 1);               // souffle grave, 0,35


  /* ===================================================================
     COUCHE 6 — 24,9 à 36,5 s : ouverture stellaire du trou noir (26 s)
     puis dissipation
     =================================================================== */

  // 6a. Éclair de bruit aigu juste avant l'ouverture (24,9 → 26 s), avec réverbération
  {
    const src = actx.createBufferSource();
    const fl  = actx.createBiquadFilter();
    const gn  = actx.createGain();
    src.buffer = noise;
    src.loop = true;
    fl.type = 'highpass';
    fl.frequency.setValueAtTime(500, t0 + 24.9);
    fl.frequency.exponentialRampToValueAtTime(9000, t0 + 26);
    gn.gain.setValueAtTime(0.0001, t0 + 24.9);
    gn.gain.exponentialRampToValueAtTime(0.3, t0 + 25.98);      // volume 0,3
    gn.gain.setValueAtTime(0.0001, t0 + 26.02);
    src.connect(fl);
    fl.connect(gn);
    gn.connect(sx);
    src.start(t0 + 24.9);
    src.stop(t0 + 26.05);
  }

  // 6b. Grave d'explosion à 26 s
  osc('sine', 62, 22, 26, 32, 0.55, 0.01, 5.5);                 // le plus fort de tout, 0,55
  burst(26, 2.6, 'lowpass', 1400, 90, 0.4, 1);                  // souffle grave, 0,4

  // 6c. Trois notes cristallines réparties dans l'espace stéréo (très discrètes)
  [880, 1318.5, 1760].forEach((f, i) =>
    osc('sine', f, f, 26, 35, 0.012, 1.2, 6, pan(-0.6 + i * 0.6)));

  // 6d. Accord de cinq harmoniques de 110 Hz (volume 0,05 chacune)
  [1, 1.5, 2, 3, 4.5].forEach((r, i) =>
    osc('sine', 110 * r, 110 * r, 26, 36, 0.05, 0.5, 8, pan(i % 2 ? 0.6 : -0.6)));

  // 6e. Deux sifflements qui descendent (aigu → grave)
  osc('sine', 2400, 300, 29,   36.5, 0.07, 0.1, 5, pan(0));
  osc('sine', 3600, 450, 29.2, 36.5, 0.04, 0.1, 5, pan(0.5));

  // 6f. 40 étincelles aiguës aléatoires (2000 à 8000 Hz), de 29 à 35 s
  for (let k = 0; k < 40; k++) {
    const ta = 29 + rnd() * 6;
    const f  = 2000 + rnd() * 6000;
    osc('sine', f, f, ta, ta + 1.2, 0.03 * (1 - (ta - 29) / 7), 0.004, 1.1, pan(rnd() * 2 - 1));
  }


  /* ===================================================================
     COUCHE 7 — 10,4 à 12,5 s : craquements à l'apparition des fractales
     =================================================================== */
  for (let i = 0; i < 20; i++) {
    const ta = 10.5 + i * 0.09 + rnd() * 0.03;
    const pn = pan(rnd() * 2 - 1);
    burst(ta, 0.14, 'bandpass', 2600 + rnd() * 1800, 500, 0.22, 3, pn);     // volume 0,22
    osc('sine', 1100 + rnd() * 600, 180, ta, ta + 0.06, 0.06, 0.001, 0.05, pn);
  }
  burst(10.4, 0.5, 'lowpass', 500, 90, 0.18, 1);                // petit coup grave au départ


  /* ===================================================================
     COUCHE 8 — 25,7 à 27,6 s : le cristal qui se brise
     (les faces du dodécaèdre se séparent)
     =================================================================== */
  burst(25.7,  0.35, 'highpass', 900,  900,  0.4,  0.7, sx);    // craquement initial, 0,4
  burst(25.72, 0.12, 'bandpass', 4200, 1500, 0.35, 2,   sx);    // claquement aigu, 0,35

  // 70 éclats de verre aigus (3500 à 9000 Hz), de 25,85 à ~27,7 s
  for (let k = 0; k < 70; k++) {
    const ta = 25.85 + Math.pow(rnd(), 1.6) * 1.9;
    const f  = 3500 + rnd() * 5500;
    const pn = pan(rnd() * 2 - 1);
    burst(ta, 0.03 + rnd() * 0.09, 'bandpass', f, f * 0.6, 0.16 * (1 - (ta - 25.8) / 2.6), 6, pn);
    if (k % 3 === 0) osc('sine', f, f * 0.8, ta, ta + 0.1, 0.02, 0.001, 0.09, pn);
  }
}


/* ---------------------------------------------------------------------
   5. DÉMARRER / ARRÊTER LE SON
   --------------------------------------------------------------------- */
function sndStart() {
  if (NOSND || MUTE) return;
  try {
    if (!SND) SND = { ctx: new (window.AudioContext || window.webkitAudioContext)() };
    const c = SND.ctx;
    c.resume();

    // Si un son précédent joue encore, on le coupe en douceur
    if (SND.chain) {
      const b = SND.chain.bus;
      b.gain.setTargetAtTime(0, c.currentTime, 0.05);
      setTimeout(() => { try { b.disconnect() } catch (e) {} }, 500);
    }

    const t0 = c.currentTime + 0.05;
    const chain = masterChain(c, c.destination);
    const { bus } = chain;

    // Volume général : MASTER, puis fondu de 38 à 40 s
    bus.gain.setValueAtTime(MASTER, t0);
    bus.gain.setValueAtTime(MASTER, t0 + FIN_FADE);
    bus.gain.linearRampToValueAtTime(0.0001, t0 + DUREE);

    SND.chain = chain;
    buildSound(c, bus, t0);
  } catch (e) {}
}

function sndStop() {
  try {
    if (SND && SND.chain) {
      const b = SND.chain.bus;
      b.gain.setTargetAtTime(0, SND.ctx.currentTime, 0.05);
      SND.chain = null;
      setTimeout(() => { try { b.disconnect() } catch (e) {} }, 500);
    }
  } catch (e) {}
}
