import math
from typing import List
import ntcore

from configuration.Configuration import Device
from Observations import CameraPoseObservation3d

class NTPublisher:
    # Instead of a single _initialized, we keep a dict of states per camera:
    _initialized_publishers = {}

    def send(
        self,
        camera_id: int,
        config: Device,
        timestamp: float,
        observation: CameraPoseObservation3d,
        fps: int,
    ):

        # Check if we have already created a set of publishers for this camera
        if camera_id not in self._initialized_publishers:
            # Create a dedicated subtable for each camera:
            # e.g. "/myDeviceId/camera_0/output", "/myDeviceId/camera_1/output"
            table = ntcore.NetworkTableInstance.getDefault().getTable(
                f"/{config.device_id}/camera_{camera_id}/output"
            )

            publishers = {}
            publishers["observations"] = table.getDoubleArrayTopic("observations").publish(
                ntcore.PubSubOptions(periodic=0, sendAll=True, keepDuplicates=True)
            )
            publishers["raw_poses"] = table.getDoubleArrayTopic("raw_poses").publish(
                ntcore.PubSubOptions(periodic=0, sendAll=True, keepDuplicates=True)
            )
            publishers["fps"] = table.getIntegerTopic("fps").publish()

            self._initialized_publishers[camera_id] = publishers

        # Retrieve the publishers for this specific camera
        publishers = self._initialized_publishers[camera_id]
        observations_publisher = publishers["observations"]
        raw_pose_publisher = publishers["raw_poses"]
        fps_publisher = publishers["fps"]

        if fps is not None:
            fps_publisher.set(fps)

        observation_data: List[float] = [0]
        raw_poses: List[float] = [0]

        if observation is not None:
            observation_data[0] = 1
            observation_data.append(observation.error)
            observation_data.append(observation.pose.translation().X())
            observation_data.append(observation.pose.translation().Y())
            observation_data.append(observation.pose.translation().Z())
            observation_data.append(observation.pose.rotation().getQuaternion().W())
            observation_data.append(observation.pose.rotation().getQuaternion().X())
            observation_data.append(observation.pose.rotation().getQuaternion().Y())
            observation_data.append(observation.pose.rotation().getQuaternion().Z())

            raw_poses[0] = observation.pose.translation().X()
            raw_poses.append(observation.pose.translation().Y())
            raw_poses.append(observation.pose.translation().Z())
            raw_poses.append(observation.pose.rotation().getQuaternion().W())
            raw_poses.append(observation.pose.rotation().getQuaternion().X())
            raw_poses.append(observation.pose.rotation().getQuaternion().Y())
            raw_poses.append(observation.pose.rotation().getQuaternion().Z())

            # If there's also alt-pose
            if observation.error_alt is not None and observation.pose_alt is not None:
                observation_data[0] = 2
                observation_data.append(observation.error_alt)
                observation_data.append(observation.pose_alt.translation().X())
                observation_data.append(observation.pose_alt.translation().Y())
                observation_data.append(observation.pose_alt.translation().Z())
                observation_data.append(observation.pose_alt.rotation().getQuaternion().W())
                observation_data.append(observation.pose_alt.rotation().getQuaternion().X())
                observation_data.append(observation.pose_alt.rotation().getQuaternion().Y())
                observation_data.append(observation.pose_alt.rotation().getQuaternion().Z())

                raw_poses.append(observation.pose_alt.translation().X())
                raw_poses.append(observation.pose_alt.translation().Y())
                raw_poses.append(observation.pose_alt.translation().Z())
                raw_poses.append(observation.pose_alt.rotation().getQuaternion().W())
                raw_poses.append(observation.pose_alt.rotation().getQuaternion().X())
                raw_poses.append(observation.pose_alt.rotation().getQuaternion().Y())
                raw_poses.append(observation.pose_alt.rotation().getQuaternion().Z())

            for tag_id in observation.tag_ids:
                observation_data.append(tag_id)

        # Send them to NT with a timestamp
        observations_publisher.set(
            observation_data,
            math.floor(timestamp * 1_000_000)
        )
        raw_pose_publisher.set(
           raw_poses,
           math.floor(timestamp * 1_000_000)
        )

