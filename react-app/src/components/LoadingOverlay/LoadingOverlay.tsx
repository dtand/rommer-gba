import React from 'react';
import { Overlay, Content, LoadingText, Spinner } from './LoadingOverlay.styled';

const LoadingOverlay: React.FC = () => (
  <Overlay>
    <Content>
      <LoadingText>Loading</LoadingText>
      <Spinner />
    </Content>
  </Overlay>
);

export default LoadingOverlay;
