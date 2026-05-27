#include "GodotOceanWavesShaders.h"

IMPLEMENT_GLOBAL_SHADER(FGodotOceanWavesPreviewCS, "/Plugin/GodotOceanWaves/Private/GodotOceanWavesPreview.usf", "MainCS", SF_Compute);
IMPLEMENT_GLOBAL_SHADER(FGodotOceanWavesSpectrumCS, "/Plugin/GodotOceanWaves/Private/GodotOceanWavesFFT.usf", "SpectrumCS", SF_Compute);
IMPLEMENT_GLOBAL_SHADER(FGodotOceanWavesButterflyCS, "/Plugin/GodotOceanWaves/Private/GodotOceanWavesFFT.usf", "ButterflyCS", SF_Compute);
IMPLEMENT_GLOBAL_SHADER(FGodotOceanWavesModulateCS, "/Plugin/GodotOceanWaves/Private/GodotOceanWavesFFT.usf", "ModulateCS", SF_Compute);
IMPLEMENT_GLOBAL_SHADER(FGodotOceanWavesFFTCS, "/Plugin/GodotOceanWaves/Private/GodotOceanWavesFFT.usf", "FFTCS", SF_Compute);
IMPLEMENT_GLOBAL_SHADER(FGodotOceanWavesTransposeCS, "/Plugin/GodotOceanWaves/Private/GodotOceanWavesFFT.usf", "TransposeCS", SF_Compute);
IMPLEMENT_GLOBAL_SHADER(FGodotOceanWavesUnpackCS, "/Plugin/GodotOceanWaves/Private/GodotOceanWavesFFT.usf", "UnpackCS", SF_Compute);
