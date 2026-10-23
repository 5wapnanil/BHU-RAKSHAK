import React from 'react';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { Ionicons } from '@expo/vector-icons';
import { colors } from '../theme/colors';
import { useLanguage } from '../i18n';

import { HomeScreen } from '../screens/HomeScreen';
import { RequestReliefScreen } from '../screens/RequestReliefScreen';
import { CallForEvacuationScreen } from '../screens/CallForEvacuationScreen';
import { VolunteerForEvacuationScreen } from '../screens/VolunteerForEvacuationScreen';
import { VolunteerForReliefScreen } from '../screens/VolunteerForReliefScreen';
import { AlertsScreen } from '../screens/AlertsScreen';
import { NearbySheltersScreen } from '../screens/NearbySheltersScreen';
import { MyRequestsScreen } from '../screens/MyRequestsScreen';
import { ProfileLoginScreen } from '../screens/ProfileLoginScreen';
import { EmergencyCenterScreen } from '../screens/EmergencyCenterScreen';
import { ContactScreen } from '../screens/ContactScreen';
import { LandslideSafetyGuideScreen } from '../screens/LandslideSafetyGuideScreen';
import { PostDisasterCheckInScreen } from '../screens/PostDisasterCheckInScreen';
import { FieldReportScreen } from '../screens/FieldReportScreen';
import {
  OperationsScreen,
  AssignmentsScreen,
  AssignmentDetailScreen,
  ReliefResourcesScreen,
  ReliefResourceDetailScreen,
  SheltersScreen,
  ShelterDetailScreen,
} from '../screens/operations';

import type { BottomTabParamList, HomeStackParamList, OperationsStackParamList, ProfileStackParamList } from './types';

const HomeStack = createNativeStackNavigator<HomeStackParamList>();
const OperationsStack = createNativeStackNavigator<OperationsStackParamList>();
const ProfileStack = createNativeStackNavigator<ProfileStackParamList>();
const Tab = createBottomTabNavigator<BottomTabParamList>();

function HomeStackNavigator({ initialRouteName }: { initialRouteName?: keyof HomeStackParamList }) {
  return (
    <HomeStack.Navigator screenOptions={{ headerShown: false }} initialRouteName={initialRouteName}>
      <HomeStack.Screen name="HomeMain" component={HomeScreen} />
      <HomeStack.Screen name="CallForEvacuation" component={CallForEvacuationScreen} />
      <HomeStack.Screen name="VolunteerForEvacuation" component={VolunteerForEvacuationScreen} />
      <HomeStack.Screen name="RequestRelief" component={RequestReliefScreen} />
      <HomeStack.Screen name="VolunteerForRelief" component={VolunteerForReliefScreen} />
      <HomeStack.Screen name="Alerts" component={AlertsScreen} />
      <HomeStack.Screen name="NearbyShelters" component={NearbySheltersScreen} />
      <HomeStack.Screen name="MyRequests" component={MyRequestsScreen} />
      <HomeStack.Screen name="EmergencyCenter" component={EmergencyCenterScreen} />
      <HomeStack.Screen name="LandslideSafetyGuide" component={LandslideSafetyGuideScreen} />
      <HomeStack.Screen name="PostDisasterCheckIn" component={PostDisasterCheckInScreen} />
      <HomeStack.Screen name="FieldReport" component={FieldReportScreen} />
    </HomeStack.Navigator>
  );
}

function SOSHomeStackNavigator() {
  return <HomeStackNavigator initialRouteName="EmergencyCenter" />;
}

function OperationsStackNavigator() {
  return (
    <OperationsStack.Navigator screenOptions={{ headerShown: false }}>
      <OperationsStack.Screen name="OperationsMain" component={OperationsScreen} />
      <OperationsStack.Screen name="Assignments" component={AssignmentsScreen} />
      <OperationsStack.Screen name="AssignmentDetail" component={AssignmentDetailScreen} />
      <OperationsStack.Screen name="ReliefResources" component={ReliefResourcesScreen} />
      <OperationsStack.Screen name="ReliefResourceDetail" component={ReliefResourceDetailScreen} />
      <OperationsStack.Screen name="Shelters" component={SheltersScreen} />
      <OperationsStack.Screen name="ShelterDetail" component={ShelterDetailScreen} />
    </OperationsStack.Navigator>
  );
}

function ProfileStackNavigator() {
  return (
    <ProfileStack.Navigator screenOptions={{ headerShown: false }}>
      <ProfileStack.Screen name="ProfileLogin" component={ProfileLoginScreen} />
    </ProfileStack.Navigator>
  );
}

export function BottomTabNavigator() {
  const { t } = useLanguage();
  return (
    <Tab.Navigator
      screenOptions={{
        headerShown: false,
        tabBarActiveTintColor: colors.primary,
        tabBarInactiveTintColor: colors.textLight,
        tabBarStyle: {
          backgroundColor: colors.white,
          borderTopColor: colors.borderLight,
          paddingBottom: 8,
          paddingTop: 8,
          height: 65,
        },
        tabBarLabelStyle: {
          fontSize: 10,
          fontWeight: '600',
        },
      }}
    >
      <Tab.Screen
        name="HomeTab"
        component={HomeStackNavigator}
        options={{
          tabBarLabel: t('tab.home'),
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="home" size={size} color={color} />
          ),
        }}
      />
      <Tab.Screen
        name="OperationsTab"
        component={OperationsStackNavigator}
        options={{
          tabBarLabel: t('tab.operations'),
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="briefcase" size={size} color={color} />
          ),
        }}
      />
      <Tab.Screen
        name="ContactTab"
        component={ContactScreen}
        options={{
          tabBarLabel: t('tab.contact'),
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="people" size={size} color={color} />
          ),
        }}
      />
      <Tab.Screen
        name="SOS"
        component={SOSHomeStackNavigator}
        options={{
          tabBarLabel: t('tab.sos'),
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="shield" size={size} color={color} />
          ),
        }}
      />
      <Tab.Screen
        name="SettingsTab"
        component={ProfileStackNavigator}
        options={{
          tabBarLabel: t('tab.settings'),
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="settings" size={size} color={color} />
          ),
        }}
      />
    </Tab.Navigator>
  );
}
