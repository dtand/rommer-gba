import React from 'react';
import FrameIdListing from '../FrameIdListing/FrameIdListing';
import { FaCheckCircle } from 'react-icons/fa';
import {
  NotificationContainer,
  IconColumn,
  IconWrapper,
  ContentColumn,
  NotificationTitle,
  CloseNotificationButton,
} from './FramesCompleteNotification.styled';

interface FramesCompleteNotificationProps {
  frameIds: number[];
  showIcon?: boolean;
  onClose?: () => void;
}

const FramesCompleteNotification: React.FC<FramesCompleteNotificationProps> = ({ frameIds, showIcon = true, onClose }) => (
  <NotificationContainer>
    <IconColumn>
      <IconWrapper>
        <FaCheckCircle size={28} color="#fff" />
      </IconWrapper>
    </IconColumn>
    <ContentColumn style={{ position: 'relative' }}>
      {onClose && (
        <CloseNotificationButton onClick={onClose} aria-label="Close notification">×</CloseNotificationButton>
      )}
      <NotificationTitle>
        {frameIds.length} Annotation{frameIds.length !== 1 ? 's' : ''} Complete
      </NotificationTitle>
      <FrameIdListing modalFrameIds={frameIds} listStyle="comma" />
    </ContentColumn>
  </NotificationContainer>
);

export default FramesCompleteNotification;
