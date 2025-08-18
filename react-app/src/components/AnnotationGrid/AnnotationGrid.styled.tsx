import styled, { css } from 'styled-components';

// Styled components for AnnotationGrid
export const GridWrapper = styled.div`
  flex: 1;
  height: calc(100vh - 64px); /* Subtract TopNavBar height */
  overflow-y: auto;
  background: #f5f6fa;
  padding: 64px;
  margin-top: 64px; /* Reset margin to avoid double spacing */
  margin-bottom: 48px; /* Add extra bottom margin to allow scrolling past final row */
  font-family: 'Inter', 'Nunito', 'Segoe UI', 'Avenir', Helvetica, Arial, sans-serif;
`;

export const Grid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 24px;
`;

export const FrameItem = styled.div<{
  $selected?: boolean;
  $hovered?: boolean;
  $complete?: boolean;
  $partial?: boolean;
  $notAnnotated?: boolean;
}>`
  background: #fff;
  border: 4px solid rgba(0, 0, 0, 0.1);
  border-radius: 12px;
  padding: 0;
  text-align: center;
  transition: border-color 0.2s;
  cursor: pointer;
  display: flex;
  align-items: stretch;
  justify-content: stretch;
  height: 100%;
  width: 100%;
  overflow: visible;
  font-family: 'Inter', 'Nunito', 'Segoe UI', 'Avenir', Helvetica, Arial, sans-serif;

  ${({ $notAnnotated }) => $notAnnotated && css`
    border-color: #d3d3d3;
  `}
  ${({ $partial }) => $partial && css`
    border-color: #ffc107;
  `}
  ${({ $complete }) => $complete && css`
    border-color: #28a745;
  `}
  ${({ $hovered }) => $hovered && css`
    border-color: #90cdf4;
    z-index: 2;
  `}
  ${({ $selected }) => $selected && css`
    border-color: #007bff;
    z-index: 3;
  `}
`;

export const FrameImage = styled.img`
  border-top-left-radius: 6px;
  border-top-right-radius: 6px;
  border-bottom-left-radius: 0;
  border-bottom-right-radius: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
`;

export const FramePlaceholder = styled.div`
  width: 100%;
  height: 100%;
  background: #eee;
  border-radius: 6px;
`;

export const FrameStatusIcon = styled.div`
  position: absolute;
  right: 0px;
  bottom: 0px;
  background: rgba(255,255,255,0.92);
  border-radius: 50%;
  padding: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 1px 4px rgba(0,0,0,0.08);
  font-size: 1.2em;
`;

export const FrameMetaRow = styled.div<{ $complete?: boolean; $partial?: boolean }>`
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  font-size: 0.92em;
  color: #444;
  min-height: 22px;
  background: ${({ $complete, $partial }) =>
    $complete ? '#e8fbe8' : $partial ? '#fff7e0' : 'transparent'};
  border-bottom-left-radius: 6px;
  border-bottom-right-radius: 6px;
`;
