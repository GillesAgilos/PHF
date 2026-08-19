SELECT
    project.status AS [Project Status],
    project.is_active AS [Project Is Active],
    project.code AS [Project Code],
    project.molecule_name AS [Project Molecule Name],

    client.status AS [Client Status],
    client.name AS [Client Name],
    client.code AS [Client Code],

    moleculetype.status AS [Molecule Type Status],
    moleculetype.type AS [Molecule Type],
    moleculetype.description AS [Molecule Type Description],

    batch.status AS [Batch Status],
    batch.is_active AS [Batch Is Active],
    batch.category AS [Batch Category],
    batch.iteration_number AS [Batch Iteration Number],
    batch.start_date AS [Batch Start Date],
    batch.end_date AS [Batch End Date],
    batch.name AS [Batch Name],
    batch.unique_id AS [Batch ID],

    process.status AS [Process Status],
    process.name AS [Process Name],
    process.code AS [Process Code],
    process.scale AS [Process Scale],
    process.version AS [Process Version],

    unitoperation.is_active AS [Unit Operation Is Active],
    unitoperation.name AS [Unit Operation Name],
    unitoperation.unit_type AS [Unit Operation Type],
    unitoperation.[order] AS [Unit Operation Order],

    step.is_active AS [Step Is Active],
    step.name AS [Step Name],
    step.[order] AS [Step Order],

    parameter.is_active AS [Parameter Is Active],
    parameter.name AS [Parameter Name],
    parameter.unit AS [Parameter Unit],
    parameter.format_type AS [Parameter Format Type],
    parameter.format_lower_range AS [Parameter Format Lower Range],
    parameter.format_upper_range AS [Parameter Format Upper Range],
    parameter.lower_proven_acceptable_range AS [Parameter Lower Proven Acceptable Range],
    parameter.upper_proven_acceptable_range AS [Parameter Upper Proven Acceptable Range],
    parameter.lower_normal_operating_range AS [Parameter Lower Normal Operating Range],
    parameter.upper_normal_operating_range AS [Parameter Upper Normal Operating Range],
    parameter.[order] AS [Parameter Order],

    parameter_result.status AS [Parameter Result Status],
    parameter_result.is_active AS [Parameter Result Is Active],
    parameter_result.comment AS [Parameter Result Comment],
    parameter_result.actual_value AS [Parameter Result Actual Value],

    sample.is_active AS [Sample Is Active],
    sample.name AS [Sample Name],

    analysis.is_active AS [Analysis Is Active],
    analysis.analysis_name AS [Analysis Name],
    analysis.format_upper_range AS [Analysis Format Upper Range],
    analysis.format_lower_range AS [Analysis Format Lower Range],
    analysis.lower_specification AS [Analysis Lower Specification],
    analysis.upper_specification AS [Analysis Upper Specification],

    analysis_result.status AS [Analysis Result Status],
    analysis_result.is_active AS [Analysis Result Is Active],
    analysis_result.actual_value AS [Analysis Result Actual Value],
    analysis_result.comment AS [Analysis Result Comment]

FROM production_process AS process
LEFT JOIN production_unitoperation AS unitoperation
    ON process.unique_id = unitoperation.process_id
LEFT JOIN production_step AS step
    ON unitoperation.unique_id = step.unit_operation_id
LEFT JOIN production_parameter AS parameter
    ON step.unique_id = parameter.step_id
LEFT JOIN batch_batch AS batch
    ON batch.process_id = process.unique_id
LEFT JOIN batch_parameterresult AS parameter_result
    ON parameter.unique_id = parameter_result.parameter_id
    AND parameter_result.batch_id = batch.unique_id
LEFT JOIN production_sample AS sample
    ON step.unique_id = sample.step_id
LEFT JOIN production_analysis AS analysis
    ON sample.unique_id = analysis.sample_id
LEFT JOIN batch_analysisresult AS analysis_result
    ON analysis.unique_id = analysis_result.analysis_id
    AND analysis_result.batch_id = batch.unique_id
LEFT JOIN referential_project AS project
    ON project.unique_id = batch.project_id
LEFT JOIN referential_client AS client
    ON client.unique_id = project.client_id
LEFT JOIN referential_moleculetype AS moleculetype
    ON moleculetype.unique_id = project.molecule_type_id


ORDER BY
    project.code,
    batch.start_date,
    batch.iteration_number,
    batch.name,
    process.code,
    process.version,
    unitoperation.[order],
    step.[order],
    parameter.[order],
    sample.name,
    analysis.analysis_name;
