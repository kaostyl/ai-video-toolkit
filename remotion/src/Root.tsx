import React from 'react';
import {Composition, CalculateMetadataFunction} from 'remotion';
import {OverlayComp, OverlayProps, CardMask} from './OverlayComp';

const calcOverlay: CalculateMetadataFunction<OverlayProps> = async ({props}) => {
  const fps = props.fps ?? 30;
  return {
    durationInFrames: Math.max(1, Math.round((props.overlay?.dur ?? 5) * fps)),
    width: props.width ?? 1920,
    height: props.height ?? 1080,
    fps,
  };
};

const sampleOverlay = {
  id: 'sample',
  type: 'schema_checklist',
  t: 0,
  dur: 8,
  color: 'gold',
  kicker: 'À RETENIR',
  rows: [
    {mark: 'cross', text: 'Courir après les 1 000 abonnés'},
    {mark: 'check', text: 'Affiliation dès le départ'},
  ],
  note: 'Tu gagnes plus vite, sans dépendre de YouTube',
};

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="Overlay"
        component={OverlayComp}
        durationInFrames={240}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{
          overlay: sampleOverlay as any,
          style: {},
          side: 'right' as const,
          width: 1920,
          height: 1080,
          fps: 30,
        }}
        calculateMetadata={calcOverlay}
      />
      <Composition
        id="CardMask"
        component={CardMask}
        durationInFrames={1}
        fps={30}
        width={806}
        height={453}
        calculateMetadata={async ({props}) => ({
          width: (props as any).width ?? 806,
          height: (props as any).height ?? 453,
        })}
      />
    </>
  );
};
