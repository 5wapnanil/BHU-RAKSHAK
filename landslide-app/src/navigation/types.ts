import type { NavigatorScreenParams } from '@react-navigation/native';

export type HomeStackParamList = {
  HomeMain: undefined;
  CallForEvacuation: undefined;
  VolunteerForEvacuation: undefined;
  RequestRelief: undefined;
  VolunteerForRelief: undefined;
  Alerts: undefined;
  NearbyShelters: undefined;
  MyRequests: undefined;
  EmergencyCenter: undefined;
  LandslideSafetyGuide: undefined;
  PostDisasterCheckIn: undefined;
  FieldReport: undefined;
};

export type OperationsStackParamList = {
  OperationsMain: undefined;
  Assignments: undefined;
  AssignmentDetail: { id: string };
  ReliefResources: undefined;
  ReliefResourceDetail: { id: string };
  Shelters: undefined;
  ShelterDetail: { id: string };
};

export type ProfileStackParamList = {
  ProfileLogin: undefined;
};

export type BottomTabParamList = {
  HomeTab: NavigatorScreenParams<HomeStackParamList>;
  OperationsTab: NavigatorScreenParams<OperationsStackParamList>;
  ContactTab: undefined;
  SOS: NavigatorScreenParams<HomeStackParamList>;
  SettingsTab: NavigatorScreenParams<ProfileStackParamList>;
};

export type RootStackParamList = {
  Splash: undefined;
  Main: undefined;
};
