# PRD: Timestamp Functionality for Character Science

**Document Version**: 1.0
**Created**: 2025-01-23
**Last Updated**: 2025-01-23
**Owner**: Development Team
**Status**: Draft

---

## Executive Summary

**Problem Statement**: Character Science currently always creates timestamped runs, making it difficult to resume interrupted evaluations or replace existing results without manual cleanup.

**Proposed Solution**: Add a `--timestamp` option that allows users to control whether runs are timestamped (creating new runs) or use existing directories (resuming or replacing previous runs).

**Success Metrics**: Users can seamlessly resume interrupted evaluations and replace existing results without manual directory management.

---

## 1. Problem Definition

### 1.1 Current State

- **Pain Points**:

  - Character Science always creates timestamped directories, making it impossible to resume interrupted evaluations
  - Users must manually clean up directories to replace existing results
  - No way to continue where a previous run left off
  - Difficult to manage multiple experimental runs without confusion

- **User Feedback**: Users need the ability to:

  - Resume interrupted evaluations without losing progress
  - Replace existing results cleanly
  - Continue evaluations from where they left off

- **Quantitative Impact**:
  - Time wasted on manual directory cleanup
  - Lost evaluation progress when runs are interrupted
  - Confusion about which results are current

### 1.2 Root Cause Analysis

- **Why does this problem exist?** The current implementation always generates timestamps to avoid conflicts, but doesn't provide flexibility for different use cases
- **What are the underlying technical/process limitations?** No mechanism to detect existing runs or provide options for handling them
- **How does this impact our core objectives?** Reduces efficiency of character science experiments and makes it harder to iterate on evaluations

### 1.3 Target Users

- **Primary Users**: Researchers running character science evaluations
- **Secondary Users**: Developers testing character configurations
- **User Personas**:
  - Research scientists who need to resume long-running evaluations
  - Developers who want to quickly replace test results
  - Analysts who need to compare different experimental runs

---

## 2. Solution Overview

### 2.1 High-Level Approach

**Core Concept**: Add a `--timestamp` boolean flag that controls whether character science runs create timestamped directories or use existing ones.

**Key Capabilities**:

- **Timestamp Mode**: When `--timestamp` is provided, creates new timestamped directories (current behavior)
- **Resume Mode**: When `--timestamp` is not provided and `--replace` is not specified, continues from existing directories
- **Replace Mode**: When `--timestamp` is not provided and `--replace` is specified, replaces existing directories

### 2.2 User Experience Flow

```
Step 1: User runs character science with --timestamp → Creates new timestamped run
Step 2: User runs character science without --timestamp → Resumes existing run
Step 3: User runs character science without --timestamp --replace → Replaces existing run
```

### 2.3 Integration Points

- **Existing Systems**: Integrates with current character science workflow and directory structure
- **Data Dependencies**: Works with existing character definitions and evaluation results
- **External APIs**: No external API changes required

---

## 3. Technical Requirements

### 3.1 Functional Requirements

| Requirement ID | Description                            | Priority    | Acceptance Criteria                                                |
| -------------- | -------------------------------------- | ----------- | ------------------------------------------------------------------ |
| FR-001         | Add --timestamp CLI argument           | Must Have   | Users can specify --timestamp flag                                 |
| FR-002         | Timestamp mode creates new directories | Must Have   | When --timestamp provided, creates timestamped directories         |
| FR-003         | Resume mode continues existing runs    | Must Have   | When --timestamp not provided, continues from existing directories |
| FR-004         | Replace mode overwrites existing runs  | Must Have   | When --replace provided, replaces existing directories             |
| FR-005         | Detect existing evaluation state       | Should Have | System detects what evaluations have been completed                |
| FR-006         | Skip completed evaluations             | Should Have | System skips already completed evaluations in resume mode          |

### 3.2 Non-Functional Requirements

- **Performance**: No significant performance impact on evaluation runs
- **Reliability**: Robust handling of directory states and partial evaluations
- **Security**: No security implications
- **Usability**: Clear CLI interface with helpful error messages
- **Compatibility**: Backward compatible with existing character science usage

### 3.3 Technical Architecture

#### 3.3.1 System Components

```
[CLI Parser] ←→ [Directory Manager] ←→ [Evaluation State Tracker] ←→ [Character Science Engine]
```

#### 3.3.2 Data Models

```python
class RunConfig:
    timestamp: Optional[str]
    replace: bool
    output_dir: Path
    resume: bool

class EvaluationState:
    character_id: str
    completed_steps: List[str]
    partial_results: Dict[str, Any]
```

#### 3.3.3 CLI Interface

```bash
# Create new timestamped run
python character_science.py --timestamp

# Resume existing run
python character_science.py

# Replace existing run
python character_science.py --replace

# Combine with other options
python character_science.py --timestamp --configs "char1,char2" --num-variations 5
```

### 3.4 Directory Structure Changes

- **New Behavior**:
  - `--timestamp`: Creates `comparison_YYYYMMDD-HHMMSS/` directories
  - No `--timestamp`: Uses existing directories or creates non-timestamped ones
- **Migration Strategy**: Existing timestamped directories remain unchanged

---

## 4. Implementation Plan

### 4.1 Development Phases

#### Phase 1: Core Timestamp Logic (Week 1)

**Deliverables**:

- [ ] Add `--timestamp` and `--replace` CLI arguments
- [ ] Implement directory management logic
- [ ] Update `generate_character_science_commands` function
- [ ] Add basic state detection

**Success Criteria**:

- CLI accepts new arguments
- Directory creation logic works correctly
- Basic timestamp vs non-timestamp behavior implemented

#### Phase 2: Resume and Replace Logic (Week 1-2)

**Deliverables**:

- [ ] Implement resume mode (continue from existing)
- [ ] Implement replace mode (overwrite existing)
- [ ] Add evaluation state detection
- [ ] Update command generation for different modes

**Success Criteria**:

- Resume mode continues from existing directories
- Replace mode cleanly overwrites existing directories
- System detects what evaluations are already complete

#### Phase 3: Integration and Testing (Week 2)

**Deliverables**:

- [ ] Integration with existing character science workflow
- [ ] Error handling for edge cases
- [ ] Documentation updates
- [ ] Test scenarios for all modes

**Success Criteria**:

- All three modes work correctly
- Error handling is robust
- Documentation is clear and complete

### 4.2 Dependencies

- **Blocking Dependencies**: None - this is an enhancement to existing functionality
- **Parallel Work**: Can be developed alongside other character science improvements
- **External Dependencies**: None

### 4.3 Resource Requirements

- **Development**: 1 developer, 1-2 weeks
- **Design**: No UI/UX work required
- **Testing**: Manual testing of different scenarios
- **Infrastructure**: No infrastructure changes required

---

## 5. Testing Strategy

### 5.1 Test Coverage

- **Unit Tests**: CLI argument parsing, directory management logic
- **Integration Tests**: Full character science workflow with different timestamp modes
- **End-to-End Tests**: Complete evaluation runs in all three modes
- **Edge Case Tests**: Partial evaluations, interrupted runs, missing directories

### 5.2 Test Scenarios

1. **New Timestamped Run**: `--timestamp` creates new directories
2. **Resume Existing Run**: No flags continues from existing directories
3. **Replace Existing Run**: `--replace` overwrites existing directories
4. **Mixed Scenarios**: Different combinations of flags
5. **Error Cases**: Missing directories, permission issues, partial states

### 5.3 Acceptance Testing

- **User Acceptance Criteria**:
  - Users can create new timestamped runs
  - Users can resume interrupted evaluations
  - Users can replace existing results cleanly
- **Performance Benchmarks**: No significant slowdown in evaluation runs
- **Error Handling**: Clear error messages for all failure modes

---

## 6. Success Metrics & KPIs

### 6.1 Primary Success Metrics

- **Metric 1**: Time saved on directory management (target: 50% reduction)
- **Metric 2**: Successful resume rate for interrupted evaluations (target: 100%)
- **Metric 3**: User satisfaction with timestamp flexibility (target: 90% positive feedback)

### 6.2 Secondary Metrics

- **User Adoption**: Percentage of users using new timestamp options
- **Error Reduction**: Fewer directory-related errors and confusion
- **Workflow Efficiency**: Faster iteration on character science experiments

### 6.3 Measurement Plan

- **Baseline**: Current time spent on manual directory management
- **Tracking**: User feedback and usage patterns
- **Review Schedule**: Weekly during development, monthly post-launch

---

## 7. Risk Assessment

### 7.1 Technical Risks

| Risk                          | Probability | Impact | Mitigation Strategy                        |
| ----------------------------- | ----------- | ------ | ------------------------------------------ |
| Directory conflicts           | Medium      | Medium | Robust conflict detection and resolution   |
| State detection errors        | Low         | High   | Comprehensive testing of evaluation states |
| Backward compatibility issues | Low         | Medium | Thorough testing with existing workflows   |

### 7.2 Business Risks

- **User Confusion**: Risk that users don't understand the new options
- **Workflow Disruption**: Risk of breaking existing automated workflows
- **Maintenance Overhead**: Additional complexity in directory management

### 7.3 Contingency Plans

- **Plan A**: Full implementation with all three modes
- **Plan B**: Simplified implementation with just timestamp vs non-timestamp
- **Plan C**: Keep current behavior as default, make new behavior opt-in

---

## 8. Launch Plan

### 8.1 Rollout Strategy

- **Alpha**: Internal testing with development team
- **Beta**: Limited testing with research team
- **Production**: Full rollout with documentation

### 8.2 Communication Plan

- **Internal**: Documentation updates and team training
- **Users**: Updated usage examples and migration guide
- **Documentation**: Clear examples of all three modes

### 8.3 Success Monitoring

- **Day 1**: Monitor for any immediate issues
- **Week 1**: Collect user feedback on new functionality
- **Month 1**: Evaluate adoption and effectiveness

---

## 9. Post-Launch

### 9.1 Maintenance Plan

- **Bug Fixes**: Quick response to any directory management issues
- **Feature Enhancements**: Potential for more sophisticated state management
- **Performance Monitoring**: Ensure no performance degradation

### 9.2 Documentation Requirements

- **User Documentation**: Updated character science usage guide
- **Technical Documentation**: API changes and implementation details
- **Examples**: Clear examples of all three modes

### 9.3 Future Iterations

- **Version 2.0**: More sophisticated evaluation state tracking
- **Integration Opportunities**: Better integration with evaluation pipelines
- **Advanced Features**: Automatic resume detection, progress indicators

---

## Appendices

### Appendix A: Current Implementation Analysis

- Current timestamp generation in `generate_character_science_commands`
- Directory structure used by character science
- Integration points with evaluation pipeline

### Appendix B: Detailed Technical Specs

- Complete CLI interface specification
- Directory management logic
- State detection algorithms

### Appendix C: Usage Examples

- Examples of all three modes
- Migration guide from current usage
- Best practices for different scenarios

---

## Document History

| Version | Date       | Author           | Changes         |
| ------- | ---------- | ---------------- | --------------- |
| 1.0     | 2025-01-23 | Development Team | Initial version |

## Approval

**Product Owner**: ********\_******** Date: ****\_****
**Engineering Lead**: ******\_****** Date: ****\_****
**Research Lead**: ********\_******** Date: ****\_****

