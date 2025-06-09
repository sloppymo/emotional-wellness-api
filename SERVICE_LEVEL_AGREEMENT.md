# Service Level Agreement (SLA)

**Effective Date: June 8, 2025**

**Version: 1.0**

This Service Level Agreement ("SLA") is part of the Terms of Service between Forest Within Therapeutic Services Professional Corporation ("Provider," "we," "us," or "our") and users of the SylvaTune platform ("Service").

## 1. Service Availability

### 1.1 Uptime Commitment
- **Professional Plan**: 99.9% uptime (8.76 hours downtime per year)
- **Enterprise Plan**: 99.95% uptime (4.38 hours downtime per year)
- **Free Tier**: No uptime guarantee

### 1.2 Scheduled Maintenance
- **Planned Maintenance**: Maximum 4 hours per month
- **Advance Notice**: 72 hours for standard maintenance, 24 hours for emergency
- **Maintenance Window**: Typically 2:00 AM - 6:00 AM Pacific Time
- **Excluded from Uptime**: Scheduled maintenance is excluded from uptime calculations

### 1.3 Emergency Maintenance
- **Definition**: Critical security patches, major bug fixes, infrastructure issues
- **Notice**: Minimum 2 hours advance notice when possible
- **Duration**: Maximum 2 hours per incident
- **Frequency**: Maximum 2 emergency maintenance windows per quarter

## 2. Performance Standards

### 2.1 Response Times
**API Endpoints:**
- **Standard Operations**: < 500ms average response time
- **Model Training**: < 30 seconds for job submission
- **File Upload**: < 5 seconds for files up to 100MB
- **Data Export**: < 60 seconds for standard exports

**Web Interface:**
- **Page Load**: < 3 seconds for standard pages
- **Interactive Elements**: < 1 second response time
- **Real-time Updates**: < 2 seconds latency

### 2.2 Throughput Limits
**Free Tier:**
- 100 API requests per hour
- 1GB data storage
- 1 concurrent training job

**Professional Plan:**
- 1,000 API requests per hour
- 10GB data storage
- 3 concurrent training jobs

**Enterprise Plan:**
- 10,000 API requests per hour
- 100GB data storage
- 10 concurrent training jobs
- Custom limits available

## 3. Support Response Times

### 3.1 Support Channels
- **Email Support**: Available 24/7
- **Priority Support**: Enterprise customers only
- **Documentation**: Always available
- **Community Forum**: Peer-to-peer support

### 3.2 Response Time Commitments
**Free Tier:**
- **General Inquiries**: 48 hours
- **Technical Issues**: 24 hours
- **Bug Reports**: 24 hours

**Professional Plan:**
- **General Inquiries**: 24 hours
- **Technical Issues**: 8 hours
- **Bug Reports**: 4 hours
- **Critical Issues**: 2 hours

**Enterprise Plan:**
- **General Inquiries**: 8 hours
- **Technical Issues**: 4 hours
- **Bug Reports**: 2 hours
- **Critical Issues**: 1 hour
- **Emergency Support**: 30 minutes

### 3.3 Issue Severity Levels
**Critical (P0):**
- Service completely unavailable
- Data loss or corruption
- Security vulnerabilities
- Response: 1 hour (Enterprise), 2 hours (Professional)

**High (P1):**
- Major feature unavailable
- Performance degradation > 50%
- Data processing errors
- Response: 4 hours (Enterprise), 8 hours (Professional)

**Medium (P2):**
- Minor feature issues
- Performance degradation < 50%
- UI/UX problems
- Response: 24 hours (Enterprise), 48 hours (Professional)

**Low (P3):**
- Cosmetic issues
- Documentation updates
- Feature requests
- Response: 72 hours (All plans)

## 4. Data Protection and Recovery

### 4.1 Backup and Recovery
**Data Backup:**
- **Frequency**: Daily automated backups
- **Retention**: 30 days for standard backups, 90 days for weekly backups
- **Encryption**: All backups encrypted at rest
- **Testing**: Monthly backup restoration tests

**Recovery Time Objectives:**
- **RTO (Recovery Time)**: 4 hours for critical data
- **RPO (Recovery Point)**: 24 hours maximum data loss
- **Disaster Recovery**: 8 hours for full service restoration

### 4.2 Data Security
**Encryption:**
- **In Transit**: TLS 1.3 encryption
- **At Rest**: AES-256 encryption
- **Key Management**: Hardware Security Modules (HSM)
- **Access Control**: Role-based access with least privilege

**Security Monitoring:**
- **24/7 Monitoring**: Automated security monitoring
- **Incident Response**: < 1 hour for security incidents
- **Vulnerability Scanning**: Weekly automated scans
- **Penetration Testing**: Quarterly third-party assessments

## 5. Service Credits

### 5.1 Credit Eligibility
Service credits are provided when we fail to meet our uptime commitments:

**Uptime Credit Schedule:**
- **99.0% - 99.9%**: 10% monthly credit
- **95.0% - 99.0%**: 25% monthly credit
- **90.0% - 95.0%**: 50% monthly credit
- **Below 90.0%**: 100% monthly credit

### 5.2 Credit Calculation
- **Monthly Plans**: Credit applied to next billing cycle
- **Annual Plans**: Credit applied as account credit or refund
- **Maximum Credit**: 100% of monthly/annual fee
- **Credit Request**: Must be submitted within 30 days of incident

### 5.3 Exclusions
Credits are not provided for:
- Scheduled maintenance
- Customer-caused outages
- Force majeure events
- Beta or preview features
- Third-party service outages

## 6. Monitoring and Reporting

### 6.1 Service Monitoring
**Real-time Monitoring:**
- Uptime and availability tracking
- Performance metrics collection
- Error rate monitoring
- Resource utilization tracking

**Alerting:**
- Automated alerts for service issues
- Escalation procedures for critical incidents
- Customer notifications for major outages
- Status page updates

### 6.2 Reporting
**Monthly Reports:**
- Uptime statistics
- Performance metrics
- Incident summaries
- Service credits issued

**Quarterly Reviews:**
- Service improvement plans
- Customer feedback analysis
- Performance trend analysis
- SLA compliance review

## 7. Customer Responsibilities

### 7.1 Technical Requirements
**Minimum Requirements:**
- Modern web browser (Chrome 90+, Firefox 88+, Safari 14+)
- Stable internet connection (5 Mbps minimum)
- JavaScript enabled
- Cookies enabled

**API Usage:**
- Implement proper error handling
- Respect rate limits
- Use authentication tokens securely
- Follow API documentation

### 7.2 Support Cooperation
**Information Required:**
- Detailed issue description
- Steps to reproduce
- Error messages and logs
- Browser/device information
- Account details (when appropriate)

**Response Times:**
- Acknowledge support requests within 24 hours
- Provide requested information within 48 hours
- Test proposed solutions within 72 hours
- Provide feedback on resolution effectiveness

## 8. Service Changes and Updates

### 8.1 Feature Updates
**Regular Updates:**
- Monthly feature releases
- 30 days advance notice for major changes
- 7 days notice for minor updates
- Backward compatibility maintained for 12 months

**Breaking Changes:**
- 90 days advance notice required
- Migration assistance provided
- Documentation updates included
- Training materials available

### 8.2 Deprecation Policy
**Feature Deprecation:**
- 12 months advance notice
- Alternative solutions provided
- Migration tools and documentation
- Extended support during transition

## 9. Force Majeure

### 9.1 Definition
Force majeure events include:
- Natural disasters
- Government actions
- Internet service provider outages
- Third-party service failures
- Acts of terrorism or war

### 9.2 Impact on SLA
- Force majeure events exclude from uptime calculations
- Reasonable efforts to restore service
- Communication within 24 hours
- Alternative solutions when possible

## 10. SLA Review and Updates

### 10.1 Review Schedule
- **Annual Review**: Comprehensive SLA review
- **Quarterly Updates**: Minor adjustments as needed
- **Customer Feedback**: Incorporated into reviews
- **Industry Standards**: Benchmarking against best practices

### 10.2 Update Process
- **Notice Period**: 30 days for material changes
- **Customer Consultation**: Feedback solicited for major changes
- **Documentation**: Updated documentation and training
- **Transition Period**: Grace period for compliance

## 11. Contact Information

### 11.1 SLA Inquiries
**General Questions:**
Email: morgan@forestwithintherapy.com
Phone: [Your Phone Number]

**Emergency Support (Enterprise Only):**
Emergency Hotline: [Emergency Phone Number]
Response: 30 minutes guaranteed

### 11.2 Escalation Process
1. **Level 1**: Standard support channels
2. **Level 2**: Support manager escalation
3. **Level 3**: Technical lead involvement
4. **Level 4**: Executive escalation

---

**This SLA is effective as of June 8, 2025 and is subject to the Terms of Service.** 