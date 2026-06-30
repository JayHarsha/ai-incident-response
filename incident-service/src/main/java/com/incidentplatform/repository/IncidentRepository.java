package com.incidentplatform.repository;

import com.incidentplatform.entity.IncidentEntity;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface IncidentRepository extends JpaRepository<IncidentEntity, Long> {

    Optional<IncidentEntity> findByIncidentId(String incidentId);

    Optional<IncidentEntity> findByTraceId(String traceId);

    List<IncidentEntity> findAllByOrderByCreatedAtDesc();

    List<IncidentEntity> findByServiceNameOrderByCreatedAtDesc(String serviceName);
}
