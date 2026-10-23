import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
  TextInput,
  Image,
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import * as ImagePicker from 'expo-image-picker';
import { colors } from '../theme/colors';
import { typography, spacing, borderRadius } from '../theme';
import { useLocalRequests } from '../hooks/useLocalRequests';
import { useCurrentLocation } from '../hooks/useCurrentLocation';
import { useLanguage } from '../i18n';

interface FieldReportScreenProps {
  navigation: any;
}

export function FieldReportScreen({ navigation }: FieldReportScreenProps) {
  const { addFieldReport, syncToBackend } = useLocalRequests();
  const { location, state: locationState, error: locationError, address, getLocation } = useCurrentLocation();
  const { t } = useLanguage();

  const [notes, setNotes] = useState('');
  const [locationName, setLocationName] = useState('');
  const [useGps, setUseGps] = useState(false);
  const [photoUri, setPhotoUri] = useState<string | null>(null);
  const [photoFileName, setPhotoFileName] = useState<string | null>(null);
  const [photoMimeType, setPhotoMimeType] = useState<string | null>(null);
  const [reporterName, setReporterName] = useState('');
  const [reporterPhone, setReporterPhone] = useState('');

  const [submitting, setSubmitting] = useState(false);
  const [syncStatusText, setSyncStatusText] = useState<string | null>(null);

  useEffect(() => {
    if (useGps && locationState === 'success' && address && !locationName) {
      setLocationName(address);
    }
  }, [useGps, locationState, address, locationName]);

  const handleGetGps = () => {
    setUseGps(true);
    getLocation();
  };

  const handleClearGps = () => {
    setUseGps(false);
  };

  const handleTakePhoto = async () => {
    try {
      const permission = await ImagePicker.requestCameraPermissionsAsync();
      if (!permission.granted) {
        Alert.alert(
          'Camera Permission Required',
          'Please grant camera permission in your device settings to take a landslide observation photo.'
        );
        return;
      }

      const result = await ImagePicker.launchCameraAsync({
        mediaTypes: ['images'],
        allowsEditing: false,
        quality: 0.8,
      });

      if (!result.canceled && result.assets && result.assets.length > 0) {
        const asset = result.assets[0];
        setPhotoUri(asset.uri);
        setPhotoFileName(asset.fileName || `photo_${Date.now()}.jpg`);
        setPhotoMimeType(asset.mimeType || 'image/jpeg');
      }
    } catch (err: any) {
      Alert.alert('Camera Error', err?.message || 'Could not open camera.');
    }
  };

  const handlePickImage = async () => {
    try {
      const permission = await ImagePicker.requestMediaLibraryPermissionsAsync();
      if (!permission.granted) {
        Alert.alert(
          'Photo Library Permission Required',
          'Please grant gallery access in your device settings to select an observation photo.'
        );
        return;
      }

      const result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ['images'],
        allowsEditing: false,
        quality: 0.8,
      });

      if (!result.canceled && result.assets && result.assets.length > 0) {
        const asset = result.assets[0];
        setPhotoUri(asset.uri);
        setPhotoFileName(asset.fileName || `photo_${Date.now()}.jpg`);
        setPhotoMimeType(asset.mimeType || 'image/jpeg');
      }
    } catch (err: any) {
      Alert.alert('Gallery Error', err?.message || 'Could not access photo library.');
    }
  };

  const handleRemovePhoto = () => {
    setPhotoUri(null);
    setPhotoFileName(null);
    setPhotoMimeType(null);
  };

  const handleSubmit = async () => {
    if (submitting) return;

    if (!notes.trim() && !photoUri) {
      Alert.alert(
        'Observation Required',
        'Please describe the observation in the notes field or attach a photograph before submitting.'
      );
      return;
    }

    setSubmitting(true);
    setSyncStatusText('Uploading');

    const gpsCoords =
      useGps && locationState === 'success' && location
        ? { latitude: location.latitude, longitude: location.longitude }
        : undefined;

    // 1. Persist locally first into the offline-capable store & queue
    const report = addFieldReport({
      notes: notes.trim() || undefined,
      locationName: locationName.trim() || undefined,
      reporterName: reporterName.trim() || undefined,
      reporterPhone: reporterPhone.trim() || undefined,
      photoUri: photoUri || undefined,
      photoFileName: photoFileName || undefined,
      photoMimeType: photoMimeType || undefined,
      gpsCoords,
    });

    // 2. Attempt immediate synchronization
    const syncResult = await syncToBackend(report);
    setSubmitting(false);

    if (syncResult.serverConfirmed) {
      setSyncStatusText('Submitted');
      Alert.alert(
        'Report Submitted',
        'Your field observation has been delivered and confirmed by the central intelligence server.',
        [{ text: 'OK', onPress: () => navigation.goBack() }]
      );
    } else {
      setSyncStatusText('Saved Offline');
      Alert.alert(
        'Saved Offline',
        'Your report has been saved to the local queue. It will automatically upload as soon as network connectivity is restored.',
        [{ text: 'OK', onPress: () => navigation.goBack() }]
      );
    }
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
    >
      <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={styles.scrollContent}>
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backBtn}>
            <Ionicons name="arrow-back" size={24} color={colors.text} />
          </TouchableOpacity>
          <Text style={styles.headerTitle}>Field Intelligence Report</Text>
          <View style={{ width: 32 }} />
        </View>

        {/* Sync Status Banner if active */}
        {syncStatusText && (
          <View style={styles.statusBanner}>
            <Ionicons
              name={
                syncStatusText === 'Submitted'
                  ? 'checkmark-circle'
                  : syncStatusText === 'Uploading'
                  ? 'cloud-upload'
                  : 'cloud-offline'
              }
              size={18}
              color={
                syncStatusText === 'Submitted'
                  ? colors.success
                  : syncStatusText === 'Uploading'
                  ? colors.info
                  : colors.warning
              }
            />
            <Text style={styles.statusBannerText}>Status: {syncStatusText}</Text>
          </View>
        )}

        {/* Guidance Box */}
        <View style={styles.infoCard}>
          <Ionicons name="information-circle-outline" size={20} color={colors.primary} />
          <Text style={styles.infoText}>
            Report slope failures, fissures, rockfall, road blockages, or ground movement. Reports without
            GPS or photo are accepted.
          </Text>
        </View>

        {/* Observation Notes */}
        <View style={styles.formGroup}>
          <Text style={styles.label}>
            Observation Notes <Text style={styles.required}>*</Text>
          </Text>
          <TextInput
            style={styles.textArea}
            placeholder="Describe what you see: cracks in soil, mudflow, road blockage, tilted trees, or structural damage..."
            placeholderTextColor={colors.textLight}
            value={notes}
            onChangeText={setNotes}
            multiline
            numberOfLines={4}
            textAlignVertical="top"
          />
        </View>

        {/* Location Section */}
        <View style={styles.formGroup}>
          <Text style={styles.label}>Location / Landmark Name (Optional)</Text>
          <TextInput
            style={styles.input}
            placeholder="e.g. NH-10 KM 42 near Teesta Bridge"
            placeholderTextColor={colors.textLight}
            value={locationName}
            onChangeText={setLocationName}
          />
        </View>

        {/* GPS Coordinates Section */}
        <View style={styles.formGroup}>
          <Text style={styles.label}>GPS Coordinates (Optional)</Text>
          <View style={styles.gpsRow}>
            <TouchableOpacity
              style={[styles.gpsButton, useGps && styles.gpsButtonActive]}
              onPress={handleGetGps}
              disabled={locationState === 'locating'}
            >
              {locationState === 'locating' ? (
                <ActivityIndicator size="small" color={colors.white} />
              ) : (
                <Ionicons name="location" size={18} color={useGps ? colors.white : colors.primary} />
              )}
              <Text style={[styles.gpsButtonText, useGps && styles.gpsButtonTextActive]}>
                {locationState === 'locating' ? 'Acquiring GPS...' : 'Use Current GPS'}
              </Text>
            </TouchableOpacity>

            {useGps && (
              <TouchableOpacity style={styles.gpsClearButton} onPress={handleClearGps}>
                <Ionicons name="close-circle" size={18} color={colors.textLight} />
                <Text style={styles.gpsClearText}>Clear GPS</Text>
              </TouchableOpacity>
            )}
          </View>

          {useGps && locationState === 'success' && location && (
            <View style={styles.gpsDisplayBox}>
              <Text style={styles.gpsDisplayText}>
                Lat: {location.latitude.toFixed(6)}, Lon: {location.longitude.toFixed(6)}
              </Text>
              {address ? <Text style={styles.gpsAddressText}>{address}</Text> : null}
            </View>
          )}

          {useGps && locationState === 'permission_denied' && (
            <Text style={styles.errorText}>
              Location permission was denied. You may proceed without GPS or enter a landmark name above.
            </Text>
          )}

          {useGps && locationState === 'error' && (
            <Text style={styles.errorText}>{locationError || 'Could not acquire GPS position.'}</Text>
          )}
        </View>

        {/* Photo Section */}
        <View style={styles.formGroup}>
          <Text style={styles.label}>Observation Photograph (Optional)</Text>
          {photoUri ? (
            <View style={styles.photoPreviewWrap}>
              <Image source={{ uri: photoUri }} style={styles.photoPreview} />
              <TouchableOpacity style={styles.removePhotoBtn} onPress={handleRemovePhoto}>
                <Ionicons name="trash" size={18} color={colors.white} />
                <Text style={styles.removePhotoText}>Remove Photo</Text>
              </TouchableOpacity>
            </View>
          ) : (
            <View style={styles.photoButtonsRow}>
              <TouchableOpacity style={styles.photoActionBtn} onPress={handleTakePhoto}>
                <Ionicons name="camera" size={20} color={colors.primary} />
                <Text style={styles.photoActionText}>Take Photo</Text>
              </TouchableOpacity>
              <TouchableOpacity style={styles.photoActionBtn} onPress={handlePickImage}>
                <Ionicons name="images" size={20} color={colors.primary} />
                <Text style={styles.photoActionText}>From Gallery</Text>
              </TouchableOpacity>
            </View>
          )}
        </View>

        {/* Reporter Information (Optional) */}
        <View style={styles.formGroup}>
          <Text style={styles.label}>Your Name (Optional)</Text>
          <TextInput
            style={styles.input}
            placeholder="Field Scout / Citizen Name"
            placeholderTextColor={colors.textLight}
            value={reporterName}
            onChangeText={setReporterName}
          />
        </View>

        <View style={styles.formGroup}>
          <Text style={styles.label}>Your Phone Number (Optional)</Text>
          <TextInput
            style={styles.input}
            placeholder="+91 98765 43210"
            placeholderTextColor={colors.textLight}
            value={reporterPhone}
            onChangeText={setReporterPhone}
            keyboardType="phone-pad"
          />
        </View>

        {/* Submit Button */}
        <TouchableOpacity
          style={[styles.submitButton, submitting && styles.submitButtonDisabled]}
          onPress={handleSubmit}
          disabled={submitting}
        >
          {submitting ? (
            <ActivityIndicator size="small" color={colors.white} />
          ) : (
            <>
              <Ionicons name="paper-plane" size={20} color={colors.white} />
              <Text style={styles.submitButtonText}>Submit Field Report</Text>
            </>
          )}
        </TouchableOpacity>

        <View style={{ height: spacing.xxxl }} />
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.backgroundLight,
  },
  scrollContent: {
    padding: spacing.md,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: spacing.sm,
    marginBottom: spacing.sm,
  },
  backBtn: {
    padding: spacing.xs,
  },
  headerTitle: {
    fontSize: typography.fontSize.lg,
    fontWeight: typography.fontWeight.bold,
    color: colors.text,
  },
  statusBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: colors.white,
    padding: spacing.sm,
    borderRadius: borderRadius.md,
    borderWidth: 1,
    borderColor: colors.borderLight,
    marginBottom: spacing.md,
  },
  statusBannerText: {
    fontSize: typography.fontSize.sm,
    fontWeight: typography.fontWeight.semiBold,
    color: colors.text,
  },
  infoCard: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 10,
    backgroundColor: '#FFF0ED',
    padding: spacing.md,
    borderRadius: borderRadius.md,
    marginBottom: spacing.md,
  },
  infoText: {
    flex: 1,
    fontSize: typography.fontSize.sm,
    color: colors.textSecondary,
    lineHeight: 18,
  },
  formGroup: {
    marginBottom: spacing.md,
  },
  label: {
    fontSize: typography.fontSize.sm,
    fontWeight: typography.fontWeight.semiBold,
    color: colors.text,
    marginBottom: spacing.xs,
  },
  required: {
    color: colors.primary,
  },
  input: {
    backgroundColor: colors.white,
    borderWidth: 1,
    borderColor: colors.borderLight,
    borderRadius: borderRadius.md,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    fontSize: typography.fontSize.md,
    color: colors.text,
  },
  textArea: {
    backgroundColor: colors.white,
    borderWidth: 1,
    borderColor: colors.borderLight,
    borderRadius: borderRadius.md,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    fontSize: typography.fontSize.md,
    color: colors.text,
    minHeight: 100,
  },
  gpsRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  gpsButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderRadius: borderRadius.md,
    borderWidth: 1,
    borderColor: colors.primary,
    backgroundColor: colors.white,
  },
  gpsButtonActive: {
    backgroundColor: colors.primary,
  },
  gpsButtonText: {
    fontSize: typography.fontSize.sm,
    fontWeight: typography.fontWeight.semiBold,
    color: colors.primary,
  },
  gpsButtonTextActive: {
    color: colors.white,
  },
  gpsClearButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  gpsClearText: {
    fontSize: typography.fontSize.sm,
    color: colors.textLight,
  },
  gpsDisplayBox: {
    marginTop: spacing.xs,
    padding: spacing.xs,
    backgroundColor: colors.backgroundGray,
    borderRadius: borderRadius.sm,
  },
  gpsDisplayText: {
    fontSize: typography.fontSize.xs,
    fontFamily: Platform.OS === 'ios' ? 'Courier' : 'monospace',
    color: colors.textSecondary,
  },
  gpsAddressText: {
    fontSize: typography.fontSize.xs,
    color: colors.textLight,
    marginTop: 2,
  },
  errorText: {
    fontSize: typography.fontSize.xs,
    color: colors.error,
    marginTop: spacing.xxs,
  },
  photoButtonsRow: {
    flexDirection: 'row',
    gap: 12,
  },
  photoActionBtn: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    backgroundColor: colors.white,
    borderWidth: 1,
    borderColor: colors.borderLight,
    borderRadius: borderRadius.md,
    paddingVertical: spacing.md,
  },
  photoActionText: {
    fontSize: typography.fontSize.sm,
    fontWeight: typography.fontWeight.semiBold,
    color: colors.text,
  },
  photoPreviewWrap: {
    alignItems: 'center',
    backgroundColor: colors.white,
    padding: spacing.sm,
    borderRadius: borderRadius.md,
    borderWidth: 1,
    borderColor: colors.borderLight,
  },
  photoPreview: {
    width: '100%',
    height: 200,
    borderRadius: borderRadius.sm,
    resizeMode: 'cover',
  },
  removePhotoBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginTop: spacing.xs,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.xs,
    backgroundColor: colors.error,
    borderRadius: borderRadius.round,
  },
  removePhotoText: {
    fontSize: typography.fontSize.xs,
    fontWeight: typography.fontWeight.semiBold,
    color: colors.white,
  },
  submitButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 10,
    backgroundColor: colors.primary,
    borderRadius: borderRadius.md,
    paddingVertical: spacing.md,
    marginTop: spacing.sm,
  },
  submitButtonDisabled: {
    opacity: 0.6,
  },
  submitButtonText: {
    fontSize: typography.fontSize.md,
    fontWeight: typography.fontWeight.bold,
    color: colors.white,
  },
});
